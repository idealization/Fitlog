from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain import ImageAnalysisJob, ImageAnalysisJobStatus


class ImageAnalysisJobRepository(Protocol):
    def list_jobs_by_status(self, status: ImageAnalysisJobStatus, limit: int = 10) -> list[ImageAnalysisJob]:
        ...

    def update_job(
        self,
        job_id: str,
        *,
        status: ImageAnalysisJobStatus | None = None,
        progress: int | None = None,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> ImageAnalysisJob:
        ...


@dataclass(frozen=True)
class ImageAnalysisWorkerResult:
    processed: bool
    reason: str
    job: ImageAnalysisJob | None = None


def process_next_image_analysis_job(repository: ImageAnalysisJobRepository) -> ImageAnalysisWorkerResult:
    queued_jobs = repository.list_jobs_by_status(ImageAnalysisJobStatus.QUEUED, limit=1)
    if not queued_jobs:
        return ImageAnalysisWorkerResult(processed=False, reason="no_queued_jobs")

    queued_job = queued_jobs[0]
    running_job = repository.update_job(
        queued_job.id,
        status=ImageAnalysisJobStatus.RUNNING,
        progress=35,
        error=None,
    )

    try:
        result = build_placeholder_analysis_result(running_job)
        quality = result["quality"]
        completion_status = (
            ImageAnalysisJobStatus.SUCCEEDED
            if isinstance(quality, dict) and quality.get("usable") is True
            else ImageAnalysisJobStatus.NEEDS_USER_REVIEW
        )
        completed_job = repository.update_job(
            running_job.id,
            status=completion_status,
            progress=100,
            result=result,
            error=None,
        )
    except Exception as error:
        failed_job = repository.update_job(
            running_job.id,
            status=ImageAnalysisJobStatus.FAILED,
            progress=100,
            error=str(error),
        )
        return ImageAnalysisWorkerResult(processed=True, reason="failed", job=failed_job)

    return ImageAnalysisWorkerResult(processed=True, reason="processed", job=completed_job)


def build_placeholder_analysis_result(job: ImageAnalysisJob) -> dict[str, object]:
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
        "provider": "fitlog_stub",
        "modelVersion": "image-analysis-worker-stub-v1",
        "source": {
            "jobId": job.id,
            "uploadId": job.upload_id,
            "storageKey": job.storage_key,
            "contentType": job.content_type,
            "requestedOperations": list(job.requested_operations),
        },
        "quality": {
            "usable": quality["usable"],
            "score": quality["score"],
            "issues": quality["issues"],
        },
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
            "category": 0.74,
            "colors": 0.68,
            "styleTags": 0.61,
            "illustration": 0.0,
        },
        "events": ["closet_item.analyzed", "closet_item.illustration.placeholder_created"],
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
        return "shoes", _first_matching(text, (("sneaker", "sneakers"), ("loafer", "loafers"), ("boot", "boots"))) or "shoes"
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
        return "accessory", _first_matching(text, (("cap", "cap"), ("hat", "hat"), ("scarf", "scarf"), ("belt", "belt"))) or "accessory"
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
    if category in {"outerwear"}:
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
    materials = [
        material
        for material in ("cotton", "linen", "denim", "wool", "leather", "nylon")
        if material in text
    ]
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
