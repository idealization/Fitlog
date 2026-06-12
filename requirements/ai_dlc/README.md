# AI-DLC 진행 현황

이 폴더는 `requirements/service_requirements.md`를 입력으로 삼아 AI-DLC 흐름에 맞춰 작성한 실행 산출물입니다.

## AI-DLC 단계 정의

현재 저장소에 별도의 AI-DLC 플러그인 설정이나 프로젝트 규칙 파일이 없으므로, 본 프로젝트에서는 저장소 문서와 테스트 가능한 작업 단위로 AI-DLC를 적용합니다.

1. Inception / Elaborate: 요구사항 해석, 문제 정의, MVP 범위, 성공 기준 확정
2. Construction / Execute: 검증 가능한 작은 단위로 구현
3. Delivery / Check: 테스트, 품질 게이트, 잔여 리스크 확인
4. Operations: 배포, 모니터링, 피드백 루프 운영

## 산출물 목록

- `00_intent.md`: 현재 intent, 진행 상태, 작업 단위 DAG
- `01_discovery_scope.md`: 제품 목표, 사용자, MVP 범위, 가정
- `02_product_flows.md`: 핵심 화면, 사용자 플로우, 기능 명세
- `03_system_architecture.md`: 권장 기술 구조, 서비스 경계, 비동기 작업 설계
- `04_ai_pipeline.md`: 이미지 인식, 일러스트 생성, 추천 모델, 트렌드 반영 설계
- `05_data_api_contracts.md`: 데이터 모델, API 초안, 이벤트/작업 계약
- `06_delivery_backlog.md`: MVP 백로그, 우선순위, 스프린트 계획
- `07_quality_risk_checklist.md`: 테스트, 보안, 개인정보, 운영 리스크 체크리스트

## 현재 결정 사항

- 서비스명: Fitlog
- 앱: iOS/Android 우선의 크로스 플랫폼 모바일 앱
- 초기 구현 방식: React Native Expo + TypeScript
- 백엔드: FastAPI + PostgreSQL + S3 호환 이미지 저장소
- 비동기 처리: Redis Queue 또는 Celery 계열 워커
- AI: MVP에서는 외부 AI API를 활용하고, 사용자 피드백/성능 데이터를 쌓은 뒤 자체 모델 여부를 재검토
- 추천: 규칙 기반 필터와 AI 랭킹을 혼합
- 현재 실행 단위: U21 Device and live provider acceptance 진행 중

## 다음 작업

1. `./scripts/start_device_dev.sh`로 Expo Go 실기기 흐름을 연다.
2. iOS 또는 Android 기기에서 카메라 촬영과 옷장 저장을 검증한다.
3. `OPENAI_API_KEY`를 설정하고 실제 이미지 분석 요청 1건을 승인한다.
4. U21 완료 명령의 device와 live-provider 게이트를 모두 통과시킨다.
