from __future__ import annotations

import base64
import json
import socket
import time
from typing import Callable, Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..domain import ImageAnalysisJob


class ImageAnalysisProvider(Protocol):
    name: str

    def analyze(self, job: ImageAnalysisJob, image_bytes: bytes) -> dict[str, object]:
        ...


class ImageAnalysisProviderError(RuntimeError):
    pass


class OpenAIProviderConfigurationError(ImageAnalysisProviderError):
    pass


class OpenAIResponsesError(ImageAnalysisProviderError):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

    @property
    def retryable(self) -> bool:
        return self.status_code is None or self.status_code in {408, 409, 429} or (self.status_code or 0) >= 500


class OpenAIResponsesClient(Protocol):
    def create_response(self, payload: dict[str, object], timeout_seconds: float) -> dict[str, object]:
        ...


class UrlLibOpenAIResponsesClient:
    def __init__(self, api_key: str, base_url: str):
        self._api_key = api_key
        self._responses_url = f"{base_url.rstrip('/')}/responses"

    def create_response(self, payload: dict[str, object], timeout_seconds: float) -> dict[str, object]:
        request = Request(
            self._responses_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise OpenAIResponsesError(
                f"OpenAI Responses API returned HTTP {error.code}: {detail}",
                status_code=error.code,
            ) from error
        except (URLError, TimeoutError, socket.timeout) as error:
            raise OpenAIResponsesError(f"OpenAI Responses API request failed: {error}") from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OpenAIResponsesError("OpenAI Responses API returned invalid JSON.") from error


class StrictOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


QualityIssue = Literal[
    "blur_detected",
    "low_light",
    "low_resolution",
    "item_occluded",
    "multiple_items",
    "not_clothing",
    "poor_framing",
]
CategoryValue = Literal["top", "bottom", "outerwear", "dress", "shoes", "bag", "accessory"]
SeasonValue = Literal["spring", "summer", "fall", "winter", "all"]
ThicknessValue = Literal["light", "medium", "heavy"]
FormalityValue = Literal["casual", "business_casual", "formal"]


class OpenAIQuality(StrictOutputModel):
    usable: bool
    score: float = Field(ge=0, le=1)
    issues: list[QualityIssue]


class OpenAIColor(StrictOutputModel):
    name: str
    hex: str
    role: Literal["primary", "secondary"]


class OpenAIDetectedAttributes(StrictOutputModel):
    category: CategoryValue
    sub_type: str = Field(alias="subType")
    colors: list[OpenAIColor]
    pattern: str
    material_guess: list[str] = Field(alias="materialGuess")
    thickness: ThicknessValue
    seasons: list[SeasonValue]
    fit: str
    formality: FormalityValue
    style_tags: list[str] = Field(alias="styleTags")


class OpenAIClosetItemDraft(StrictOutputModel):
    name: str
    category: CategoryValue
    sub_type: str = Field(alias="subType")
    seasons: list[SeasonValue]
    style_tags: list[str] = Field(alias="styleTags")
    colors: list[str]
    thickness: ThicknessValue
    formality: FormalityValue
    status: Literal["available"]
    warmth: int = Field(ge=1, le=10)
    rain_safe: bool = Field(alias="rainSafe")
    breathability: int = Field(ge=1, le=10)


class OpenAIConfidence(StrictOutputModel):
    category: float = Field(ge=0, le=1)
    colors: float = Field(ge=0, le=1)
    style_tags: float = Field(alias="styleTags", ge=0, le=1)


class OpenAIAnalysisOutput(StrictOutputModel):
    quality: OpenAIQuality
    detected_attributes: OpenAIDetectedAttributes = Field(alias="detectedAttributes")
    closet_item_draft: OpenAIClosetItemDraft = Field(alias="closetItemDraft")
    confidence: OpenAIConfidence


class OpenAIImageAnalysisProvider:
    name = "openai"
    supported_content_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
        max_retries: int,
        client: OpenAIResponsesClient | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if not api_key.strip():
            raise OpenAIProviderConfigurationError("OPENAI_API_KEY is required for the OpenAI image analysis provider.")
        if timeout_seconds <= 0:
            raise OpenAIProviderConfigurationError("Image analysis timeout must be greater than zero.")
        if max_retries < 0:
            raise OpenAIProviderConfigurationError("Image analysis max retries cannot be negative.")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._client = client or UrlLibOpenAIResponsesClient(api_key, base_url)
        self._sleep = sleep

    def analyze(self, job: ImageAnalysisJob, image_bytes: bytes) -> dict[str, object]:
        if not image_bytes:
            raise ImageAnalysisProviderError("Uploaded image object is empty.")
        if job.content_type not in self.supported_content_types:
            raise ImageAnalysisProviderError(f"Unsupported image content type for OpenAI vision: {job.content_type}")

        response = self._create_response(self._build_request(job, image_bytes))
        output_text = _extract_response_output_text(response)
        try:
            analysis = OpenAIAnalysisOutput.model_validate_json(output_text)
        except ValidationError as error:
            raise ImageAnalysisProviderError(
                "OpenAI vision response did not match the Fitlog analysis schema."
            ) from error

        core = analysis.model_dump(by_alias=True)
        confidence = dict(core["confidence"])
        confidence["illustration"] = 0.0
        return {
            "provider": self.name,
            "modelVersion": self._model,
            "source": {
                "jobId": job.id,
                "uploadId": job.upload_id,
                "storageKey": job.storage_key,
                "contentType": job.content_type,
                "requestedOperations": list(job.requested_operations),
            },
            "quality": core["quality"],
            "detectedAttributes": core["detectedAttributes"],
            "closetItemDraft": core["closetItemDraft"],
            "illustration": {
                "status": "placeholder",
                "storageKey": f"illustrations/{job.id}.png",
                "style": "flat-fashion-illustration",
                "background": "transparent",
            },
            "confidence": confidence,
            "events": ["closet_item.analyzed", "closet_item.illustration.placeholder_created"],
        }

    def _create_response(self, payload: dict[str, object]) -> dict[str, object]:
        for attempt in range(self._max_retries + 1):
            try:
                return self._client.create_response(payload, self._timeout_seconds)
            except OpenAIResponsesError as error:
                if not error.retryable or attempt >= self._max_retries:
                    raise
                self._sleep(0.25 * (2**attempt))
        raise AssertionError("OpenAI retry loop exited unexpectedly.")

    def _build_request(self, job: ImageAnalysisJob, image_bytes: bytes) -> dict[str, object]:
        image_data = base64.b64encode(image_bytes).decode("ascii")
        return {
            "model": self._model,
            "store": False,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": _OPENAI_VISION_PROMPT},
                        {
                            "type": "input_image",
                            "image_url": f"data:{job.content_type};base64,{image_data}",
                            "detail": "high",
                        },
                    ],
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "fitlog_clothing_analysis",
                    "strict": True,
                    "schema": OpenAIAnalysisOutput.model_json_schema(by_alias=True),
                }
            },
            "max_output_tokens": 1800,
        }


_OPENAI_VISION_PROMPT = """Analyze the single clothing item in this image for a digital wardrobe.
Evaluate image quality first. Use only the allowed issue codes.
Extract conservative visual attributes without guessing a brand.
Use English lowercase tokens for categorical values and style tags. Create a short user-facing item name.
Warmth and breathability must be integers from 1 to 10. Confidence values must be between 0 and 1.
If the image is unusable, still return the best available draft and list every relevant quality issue."""


def _extract_response_output_text(response: dict[str, object]) -> str:
    output = response.get("output")
    if not isinstance(output, list):
        raise ImageAnalysisProviderError("OpenAI vision response did not include output items.")
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str):
                return part["text"]
    raise ImageAnalysisProviderError("OpenAI vision response did not include structured output text.")


class DeterministicImageAnalysisProvider:
    name = "demo"

    def analyze(self, job: ImageAnalysisJob, image_bytes: bytes) -> dict[str, object]:
        if not image_bytes:
            raise ValueError("Uploaded image object is empty.")
        return build_deterministic_analysis_result(job)


def build_image_analysis_provider(
    provider_name: str,
    *,
    openai_api_key: str | None = None,
    openai_model: str = "gpt-5.4-mini",
    openai_base_url: str = "https://api.openai.com/v1",
    timeout_seconds: float = 30.0,
    max_retries: int = 2,
) -> ImageAnalysisProvider:
    normalized_name = provider_name.strip().lower()
    if normalized_name in {DeterministicImageAnalysisProvider.name, "deterministic"}:
        return DeterministicImageAnalysisProvider()
    if normalized_name == OpenAIImageAnalysisProvider.name:
        return OpenAIImageAnalysisProvider(
            api_key=openai_api_key or "",
            model=openai_model,
            base_url=openai_base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
    raise ValueError(f"Unsupported image analysis provider: {provider_name}")


def build_deterministic_analysis_result(job: ImageAnalysisJob) -> dict[str, object]:
    text = f"{job.original_file_name} {job.storage_key}".lower()
    category, sub_type = _infer_category(text)
    colors = _infer_colors(text)
    thickness = _infer_thickness(text, category)
    seasons = _infer_seasons(thickness, category)
    style_tags = _infer_style_tags(text, category)
    quality = _infer_quality(text)

    primary_color = colors[0]["name"]
    item_name = _display_name(job.original_file_name, primary_color, sub_type)
    closet_item_draft = {
        "name": item_name,
        "category": category,
        "subType": sub_type,
        "seasons": seasons,
        "styleTags": style_tags,
        "colors": [color["name"] for color in colors],
        "thickness": thickness,
        "formality": _infer_formality(text),
        "status": "available",
        "warmth": _infer_warmth(thickness, category),
        "rainSafe": _infer_rain_safe(text, category),
        "breathability": _infer_breathability(thickness, category),
    }

    return {
        "provider": "fitlog_demo",
        "modelVersion": "demo-metadata-draft-v1",
        "source": {
            "jobId": job.id,
            "uploadId": job.upload_id,
            "storageKey": job.storage_key,
            "contentType": job.content_type,
            "requestedOperations": list(job.requested_operations),
        },
        "quality": quality,
        "detectedAttributes": {
            "category": category,
            "subType": sub_type,
            "colors": colors,
            "pattern": _infer_pattern(text),
            "materialGuess": _infer_materials(text, category),
            "thickness": thickness,
            "seasons": seasons,
            "fit": _infer_fit(text),
            "formality": closet_item_draft["formality"],
            "styleTags": style_tags,
        },
        "closetItemDraft": closet_item_draft,
        "illustration": {
            "status": "placeholder",
            "storageKey": f"illustrations/{job.id}.png",
            "style": "flat-fashion-illustration",
            "background": "transparent",
        },
        "confidence": {
            "category": 1.0,
            "colors": 1.0,
            "styleTags": 0.5,
            "illustration": 0.0,
        },
        "events": ["closet_item.demo_draft_created", "closet_item.illustration.placeholder_created"],
    }


def _infer_quality(text: str) -> dict[str, object]:
    issues: list[str] = []
    if _contains_any(text, ("blurry", "blurred", "out-of-focus")):
        issues.append("blur_detected")
    if _contains_any(text, ("dark", "low-light", "underexposed")):
        issues.append("low_light")
    if _contains_any(text, ("tiny", "low-resolution", "pixelated")):
        issues.append("low_resolution")

    score = max(0.25, 0.92 - (0.24 * len(issues)))
    return {
        "usable": not issues,
        "score": round(score, 2),
        "issues": issues,
    }


def _infer_category(text: str) -> tuple[str, str]:
    if _contains_any(text, ("dress", "onepiece")):
        return "dress", "dress"
    if _contains_any(text, ("sneaker", "loafer", "boot", "shoe", "sandals")):
        return "shoes", _first_matching(
            text,
            (("sneaker", "sneakers"), ("loafer", "loafers"), ("boot", "boots")),
        ) or "shoes"
    if _contains_any(text, ("pants", "slacks", "jeans", "denim", "skirt", "shorts")):
        return "bottom", _first_matching(
            text,
            (("slacks", "slacks"), ("jeans", "jeans"), ("denim", "jeans"), ("skirt", "skirt"), ("shorts", "shorts")),
        ) or "pants"
    if _contains_any(text, ("coat", "jacket", "blazer", "cardigan", "parka")):
        return "outerwear", _first_matching(
            text,
            (("coat", "coat"), ("blazer", "blazer"), ("cardigan", "cardigan"), ("parka", "parka")),
        ) or "jacket"
    if _contains_any(text, ("bag", "tote", "backpack")):
        return "bag", _first_matching(text, (("tote", "tote"), ("backpack", "backpack"))) or "bag"
    if _contains_any(text, ("cap", "hat", "scarf", "belt", "watch")):
        return "accessory", _first_matching(
            text,
            (("cap", "cap"), ("hat", "hat"), ("scarf", "scarf"), ("belt", "belt")),
        ) or "accessory"
    return "top", _first_matching(
        text,
        (
            ("shirt", "shirt"),
            ("blouse", "blouse"),
            ("tee", "t-shirt"),
            ("tshirt", "t-shirt"),
            ("knit", "knit"),
            ("sweater", "sweater"),
            ("hoodie", "hoodie"),
        ),
    ) or "top"


def _infer_colors(text: str) -> list[dict[str, str]]:
    color_keywords = (
        ("white", "#FFFFFF", ("white", "ivory", "cream")),
        ("black", "#111111", ("black",)),
        ("navy", "#1F2A44", ("navy",)),
        ("blue", "#2F80ED", ("blue", "denim")),
        ("gray", "#8A8F98", ("gray", "grey")),
        ("beige", "#D8C3A5", ("beige", "khaki", "tan")),
        ("brown", "#7A5230", ("brown", "camel")),
        ("green", "#3E7A50", ("green", "olive")),
        ("red", "#C94343", ("red", "burgundy")),
    )
    matches = [
        {"name": name, "hex": hex_value, "role": "primary" if index == 0 else "secondary"}
        for index, (name, hex_value, keywords) in enumerate(
            (entry for entry in color_keywords if _contains_any(text, entry[2]))
        )
    ]
    return matches or [{"name": "neutral", "hex": "#B8B3A8", "role": "primary"}]


def _infer_thickness(text: str, category: str) -> str:
    if _contains_any(text, ("coat", "parka", "puffer", "wool", "boot")):
        return "heavy"
    if _contains_any(text, ("linen", "shorts", "tee", "tshirt", "sandals")):
        return "light"
    if category == "outerwear":
        return "heavy"
    return "medium"


def _infer_seasons(thickness: str, category: str) -> list[str]:
    if category in {"bag", "accessory", "shoes"}:
        return ["all"]
    if thickness == "heavy":
        return ["fall", "winter"]
    if thickness == "light":
        return ["spring", "summer"]
    return ["all"]


def _infer_style_tags(text: str, category: str) -> list[str]:
    tags: list[str] = []
    if _contains_any(text, ("white", "black", "navy", "gray", "grey", "shirt", "slacks")):
        tags.append("minimal")
    if _contains_any(text, ("slacks", "shirt", "blazer", "loafer")):
        tags.append("workwear")
    if _contains_any(text, ("denim", "jeans", "sneaker", "tee", "tshirt", "hoodie")):
        tags.append("casual")
    if _contains_any(text, ("coat", "loafer", "blazer", "wool")):
        tags.append("classic")
    if category in {"bag", "accessory"}:
        tags.append("accent")
    return tags or ["daily"]


def _infer_formality(text: str) -> str:
    if _contains_any(text, ("suit", "formal")):
        return "formal"
    if _contains_any(text, ("shirt", "slacks", "blazer", "loafer", "coat")):
        return "business_casual"
    return "casual"


def _infer_warmth(thickness: str, category: str) -> int:
    if category in {"bag", "accessory"}:
        return 1
    if thickness == "heavy":
        return 8
    if thickness == "light":
        return 3
    if category == "shoes":
        return 2
    return 5


def _infer_breathability(thickness: str, category: str) -> int:
    if category in {"bag", "accessory"}:
        return 5
    if thickness == "light":
        return 8
    if thickness == "heavy":
        return 4
    return 6


def _infer_rain_safe(text: str, category: str) -> bool:
    return category == "shoes" and _contains_any(text, ("boot", "rain", "waterproof"))


def _infer_pattern(text: str) -> str:
    if _contains_any(text, ("stripe", "striped")):
        return "stripe"
    if _contains_any(text, ("check", "plaid")):
        return "check"
    if _contains_any(text, ("dot", "polka")):
        return "dot"
    return "solid"


def _infer_materials(text: str, category: str) -> list[str]:
    materials = [material for material in ("cotton", "linen", "denim", "wool", "leather", "nylon") if material in text]
    if materials:
        return materials
    if category == "shoes":
        return ["leather"]
    if category == "outerwear":
        return ["wool"]
    return ["cotton"]


def _infer_fit(text: str) -> str:
    if _contains_any(text, ("oversize", "oversized")):
        return "oversized"
    if _contains_any(text, ("slim", "skinny")):
        return "slim"
    if _contains_any(text, ("wide", "loose")):
        return "relaxed"
    return "regular"


def _display_name(file_name: str, primary_color: str, sub_type: str) -> str:
    stem = file_name.rsplit(".", maxsplit=1)[0].replace("-", " ").replace("_", " ").strip()
    if stem:
        return stem[:80]
    if primary_color == "neutral":
        return sub_type.title()
    return f"{primary_color.title()} {sub_type.title()}"


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _first_matching(text: str, matches: tuple[tuple[str, str], ...]) -> str | None:
    for keyword, value in matches:
        if keyword in text:
            return value
    return None
