---
name: dual-environment-sync-workflow
description: 강의실(계정 hi)과 집 데스크톱(계정 User) 두 PC를 오가며 작업 — 메모리 폴더 수동 복사 + git으로 매일 동기화하는 반복 루틴
metadata:
  node_type: memory
  type: project
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

사용자는 **강의실 PC(계정명 `hi`)** 와 **집 데스크톱(계정명 `User`)** 을 오가며 이 프로젝트를 작업한다 (2026-06-08 확인). 매번 다음 루틴을 반복함:

## 동기화 루틴
1. 한쪽에서 작업 종료 → `.claude/projects/c--Users-{계정}-Desktop-k8sE-commerce` (메모리 폴더) 압축
2. 프로젝트 코드는 git commit & push
3. 다른쪽 PC의 `C:\Users\{계정}\.claude\projects\c--Users-{계정}-Desktop-k8sE-commerce` 경로에 압축 파일을 덮어쓰기
4. git pull로 코드 동기화
5. 작업 진행
6. (다음날) 위 과정을 반대 방향으로 반복

## 핵심 포인트
- **메모리 폴더 경로가 계정명 때문에 서로 다름**: 집은 `C:\Users\User\.claude\projects\c--Users-User-Desktop-k8sE-commerce`, 강의실은 `C:\Users\hi\.claude\projects\c--Users-hi-Desktop-k8sE-commerce`로 추정됨 (폴더명에 절대경로가 인코딩되는 방식이라 계정명이 다르면 폴더명도 달라짐)
- 코드(git)와 메모리(수동 압축/복사)는 **별도의 동기화 경로**를 탐 — git만 동기화되고 메모리 폴더 복사를 깜빡하면 두 환경의 기억이 어긋날 수 있음
- 메모리는 매번 "덮어쓰기"이므로, 최신 작업 PC의 메모리가 항상 기준(source of truth)이 됨 — 두 환경에서 동시에 작업하지 않는 한 충돌 위험은 낮음

**Why**: 사용자가 일정/루틴을 명시적으로 설명하며 "이런식일거 같은데"라고 공유함. 앞으로 세션에서 "메모리를 옮겼다", "방금 강의실/집에서 가져왔다" 같은 말이 나오면 이 루틴을 가리키는 것으로 이해하면 됨.

**How to apply**:
- 세션 시작 시 평소와 다른 점(예: 메모리에 없는 작업 흔적이 git에 있거나 그 반대)이 보이면, "동기화 루틴 중 한 단계가 누락된 것 아닐지" 의심하고 git log/현재 코드 상태로 진실을 확인할 것 ([[feedback-proactive-memory-upkeep]]과 연결 — 메모리보다 실제 코드/git 상태가 우선)
- 작업 디렉터리 경로나 사용자명이 이전 세션과 다르게 보여도(`hi` vs `User`) 같은 프로젝트의 다른 환경일 뿐이니 당황하지 말 것
