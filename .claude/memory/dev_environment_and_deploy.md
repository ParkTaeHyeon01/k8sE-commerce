---
name: dev-environment-and-deploy
description: 개발 환경(로컬 PC)과 실제 배포 환경(VirtualBox VM 실습 / 별도 컴퓨터의 k8s VM)이 분리되어 있음 — 로컬 e2e 테스트용으로 Kafka/MongoDB를 직접 설치해 운영 중
metadata: 
  node_type: memory
  type: project
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

사용자의 개발/배포 환경 구조:

## 환경 분리
- **현재 작업 중인 PC(집)**: 개발 환경. VirtualBox VM에서 수업 실습 진행
- **강의실 PC(`hi` 계정)**: 별도 환경, 메모리 폴더 수동 동기화 필요 ([[dual-environment-sync-workflow]])
- **프로젝트용 k8s**: 또 다른 컴퓨터에 있는 VM
- **발표/배포**: 이미지를 만들어서 k8s에 배포하는 방식

## 로컬 e2e 테스트 환경 구축 (2026-06-08, 결정 변경 — 중요)
사용자가 "로컬 end-to-end 테스트가 필요하다"고 명시적으로 결정 — 과거에 "로컬에 Kafka 설치 제안 금지"였던 방침을 **뒤집고** 직접 설치/운영하기로 함.

- **Kafka 4.3.0 (KRaft 모드)**: `C:\kafka`에 설치 완료, `localhost:9092`에서 실행 중 (클러스터 UUID `AA6zj3dBQK2GI0hxyAUIlQ`). 실행은 `bin\windows\kafka-server-start.bat config\server.properties` (포그라운드 프로세스 — PC 재시작 시 수동으로 다시 켜야 함)
- **MongoDB**: ⚠️ **이전 메모(8.2 설치되어 있음)는 부정확했음 — 실제로는 이 PC에 설치되어 있지 않았음** (강의실 PC 얘기였을 가능성). 8.3.2 네이티브(Windows) 설치 시도 → **MongoDB 8.0+는 Windows 10을 공식 지원하지 않아**(`STATUS_ENTRYPOINT_NOT_FOUND`/`0xc0000139` 에러로 mongod.exe 자체가 기동 불가) 실패 → **WSL2(Ubuntu 26.04) 안에 Linux용 MongoDB 8.3.2를 설치하는 방식으로 전환 완료**
  - WSL2 활성화(Microsoft-Windows-Subsystem-Linux, VirtualMachinePlatform) → 재부팅 → Ubuntu 26.04 설치, 기본 사용자 `devuser`
  - apt 저장소: noble(24.04)용 `mongodb-org/8.3` 라인 사용 (26.04는 아직 공식 미지원이라 noble 저장소로 설치, GPG 키는 8.3 전용이 없어 8.0 키 공유 사용 — 정상)
  - WSL에 systemd 없음 → `mongod --config /etc/mongod.conf --fork`로 직접 기동 (재부팅/WSL 재시작 시 수동으로 다시 실행 필요)
  - 인증 활성화 완료: `/etc/mongod.conf`에 `security.authorization: enabled` 추가, 관리자 계정 `admin`/`k8spass#` (root 롤) 생성
  - **WSL2의 자동 localhost 포트포워딩으로 Windows에서도 `localhost:27017` 그대로 접속 가능** (mongosh, 드라이버 등에서 추가 설정 불필요)
- 사용자 의견: "localhost로 접속만 되면 되고, 안의 데이터는 나중에 덤프 떠서 강의실 PC로 옮기면 된다"

## 로컬 MongoDB 실행/접속 방법 (재부팅 후 매번 필요)
```
wsl -d Ubuntu -u root -- mongod --config /etc/mongod.conf --fork
```
접속: `mongodb://admin:k8spass%23@localhost:27017/?authSource=admin` (비밀번호의 `#`은 URL에서 `%23`로 인코딩 필요)

## 작업 방식에 대한 함의
- 코드는 Kafka 브로커 주소, MongoDB 접속 정보 등을 **환경변수로 주입받도록 작성**해서 어떤 환경(로컬/VM/k8s)에 배포되든 동작하게 구성

## 작업 순서 (업데이트 2026-06-10)
- **이미지 빌드 단계 진입**: 기능 구현 완료 후 Dockerfile 작성 단계에 진입함
- `docker/` 디렉터리에 7개 서비스 Dockerfile + ConfigMap/Secret YAML 작성 완료
- Docker Desktop 미설치 상태 → 이미지 빌드는 Docker Desktop 설치 후 진행
- 자세한 현황은 [[docker-k8s-progress]] 참고

**How to apply**: 이제 Dockerfile/이미지 빌드 작업을 자유롭게 진행해도 됨. 로컬 Kafka/MongoDB 설치·운영은 이제 진행 중인 작업이므로 막지 말 것. [[project-scope-and-role]], [[architecture_decisions]], [[docker-k8s-progress]]와 함께 참고.
