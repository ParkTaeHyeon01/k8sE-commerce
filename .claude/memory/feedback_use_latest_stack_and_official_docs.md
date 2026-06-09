---
name: feedback-use-latest-stack-and-official-docs
description: 기술 스택/라이브러리 버전은 가능한 한 최신으로 선택하고, 선택 전 공식 문서를 확인할 것 (학습 데이터의 오래된 정보에 의존하지 않기)
metadata:
  node_type: memory
  type: feedback
  originSessionId: 51a360da-2793-4782-ae28-44b40057d280
---

사용자가 "앞으로도 기술 스택들은 가능한 한 최신으로 하고 공식 도큐먼트를 참고 하도록 해"라고 명시적으로 요청함 (2026-06-08).

## 적용 방식
- 새 라이브러리/런타임/서버를 도입할 때는 (가능하면 WebSearch/WebFetch로) **최신 안정 버전을 확인**한 뒤 선택할 것 — 학습 데이터에 박제된 오래된 버전 정보를 그대로 쓰지 않기
- 설치/설정 절차도 **공식 문서 기준**으로 안내할 것 (예: Kafka는 4.x부터 ZooKeeper가 완전히 제거되고 KRaft 모드만 지원하는 등, 메이저 버전이 바뀌면 절차 자체가 달라짐)
- 예시: Kafka를 "3.x + Zookeeper" 기준으로 안내했다면 시대에 뒤떨어진 답변이 됨 — 실제로 2026-06-08 기준 최신은 4.3.0이며 KRaft 전용

**Why**: 어시스턴트의 학습 데이터 컷오프(2025-08) 이후로 기술 스택이 계속 변하기 때문에, 버전/설정 방법을 추측하면 실제와 어긋날 위험이 큼. 발표용 프로젝트에서 이런 어긋남은 신뢰도를 떨어뜨림.

**How to apply**: Kafka, MongoDB, Python 라이브러리(playwright, pymongo, kafka 클라이언트 등), k8s 관련 도구를 다룰 때마다 버전 확정 전에 검색으로 최신 상태를 확인하는 습관을 유지할 것. [[dev-environment-and-deploy]]·[[crawler-multi-instance-plan]] 등 버전이 명시된 기존 메모도 시간이 지나면 재확인이 필요할 수 있음을 인지할 것.
