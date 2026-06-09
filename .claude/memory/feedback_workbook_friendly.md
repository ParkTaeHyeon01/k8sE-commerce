---
name: feedback-workbook-friendly
description: 작업물은 항상 워크북(문서화) 산출과 팀원이 따라하기 쉬운 형태를 염두에 두고 진행할 것
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

앞으로 k8sE-commerce 작업을 할 때, 강사가 요구한 **워크북(.doc/노션) 산출물**과 **다른 팀원이 따라할 수 있는 쉬운 구조**를 항상 염두에 둘 것.

**Why**: [[project-scope-and-role]]에 정리된 강사 지침에 "산출물: 워크북(.doc/노션)"이 포함되어 있고, 사용자가 "다른 사람이 따라할 수 있도록 쉬워야 한다"고 명시적으로 요청함. 발표/시연 프로젝트는 코드가 동작하는 것만으로는 부족하고, 과정을 설명할 수 있어야 함.

**How to apply**:
- 각 서비스/모듈 작업 시 실행 방법·환경설정·의존성을 정리하기 쉬운 형태로 구성 (예: requirements.txt, README성 안내, 단계별 스크립트)
- 복잡한 설계보다 단순하고 설명하기 쉬운 구조를 우선 (이미 [[project-scope-and-role]]의 MVP 원칙과도 일치)
- 코드/설정 작업과 함께 "왜 이렇게 했는지, 어떻게 재현하는지"를 짧게라도 정리해두면 나중에 워크북으로 옮기기 수월함
- 과도한 추상화나 암묵적 관례보다는, 명시적이고 따라가기 쉬운 흐름을 선택할 것
