---
name: feedback-stay-within-directory-scope
description: 작업 시 요청받은 디렉터리/서비스 영역을 넘어서는 코드를 만들지 말 것 (예: 크롤러 작업 중 Kafka consumer가 Backend에 생성됨)
metadata:
  node_type: memory
  type: feedback
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

작업 단위(디렉터리/서비스)를 명확히 분리해서 진행할 것 — 한 영역 작업 중에 다른 서비스 영역으로 코드가 넘어가지 않도록 한다.

**Why**: 사용자가 "각 작업마다 디렉터리 영역을 넘어가지 않도록 하고 싶다"고 명시적으로 요청. 실제로 Crawler 작업 흐름에서 Kafka producer뿐 아니라 그 반대편(consumer)이 Backend/product에 함께 만들어졌던 사례가 있었고, 사용자는 이런 식으로 작업 범위가 섞이는 것을 피하고 싶어함. 기능 구현을 다 끝낸 뒤 이미지를 만들 계획([[dev-environment-and-deploy]])과도 맞물려, 작업 단계/영역이 뒤섞이면 나중에 정리하기 어려워짐.

**How to apply**:
- 특정 디렉터리(예: `Crawler/`)에서 작업을 요청받으면, 그 안에서 끝나는 코드만 작성한다. 짝이 되는 반대편 컴포넌트(예: Kafka consumer, 백엔드 저장 로직)가 필요해 보여도 먼저 사용자에게 확인 후 별도 작업으로 진행할 것
- 여러 서비스에 걸친 기능이 필요하면, "이 작업은 A와 B 두 영역에 걸쳐있는데 어떻게 나눌까요?"처럼 먼저 범위를 묻고 진행
- [[feedback-workbook-friendly]]의 "단순하고 따라가기 쉬운 구조" 원칙과도 일치 — 영역이 분리되어 있어야 팀원이 자기 담당 부분만 보고 따라가기 쉬움
