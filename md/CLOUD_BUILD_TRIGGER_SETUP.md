# Cloud Build 트리거 설정 가이드 (GitHub push → GCR → Cloud Run)

GitHub 저장소 `rokafpilot/smartbrief`에 push할 때마다 자동으로 이미지를 빌드하고 Artifact Registry에 푸시한 뒤 Cloud Run에 배포되도록 설정하는 방법입니다.

---

## 사전 조건

- GCP 프로젝트가 있고, **한 번이라도** `deploy_mac xxx.sh`로 배포해 본 상태 (Artifact Registry 저장소, Cloud Run 서비스, 환경 변수 등이 이미 있어야 함)
- 해당 프로젝트에서 **Cloud Build API** 사용 설정됨
- GitHub 저장소 **rokafpilot/smartbrief** 가 있음

---

## 1단계: GCP 콘솔에서 Cloud Build 트리거 열기

1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 상단 **프로젝트 선택**에서 사용할 프로젝트 선택 (예: `smartbrief-490302`)
3. 왼쪽 메뉴(≡) → **CI/CD** → **Cloud Build** → **트리거**
   - 또는 직접: [Cloud Build 트리거](https://console.cloud.google.com/cloud-build/triggers)
4. **트리거 만들기** 버튼 클릭

---

## 2단계: 이벤트 선택

1. **이벤트** 섹션에서 **내 저장소에 푸시할 때** 선택
2. **소스**에서 **저장소 연결** (또는 **새 저장소 연결**)

---

## 3단계: GitHub 저장소 연결 (최초 1회)

1. **저장소 소스** 선택:
   - **GitHub (Cloud Build GitHub 앱)** 또는 **GitHub(미러)** 중 사용 가능한 것 선택
2. **연결** 드롭다운:
   - 이미 연결이 있으면 해당 연결 선택
   - 없으면 **GitHub에 연결** 클릭
3. **GitHub에 연결** 시:
   - GitHub 로그인/인증 안내에 따라 진행
   - **저장소 액세스**에서 **smartbrief** 저장소만 선택하거나, 해당 조직/계정 선택
   - **연결** 완료
4. 연결 후 **저장소** 드롭다운에서 **rokafpilot/smartbrief** 선택 (또는 표시되는 경로로 선택)

---

## 4단계: 브랜치·소스 설정

1. **브랜치**:
   - **정규식** 선택 후 `^main$` 입력  
     (또는 **특정 브랜치**에서 `main` 선택)
   - `main`에 push할 때만 빌드되도록 하려면 이렇게 설정
2. **구성**:
   - **Cloud Build 구성 파일 (yaml 또는 json)** 선택
   - **위치**: **저장소** 선택
   - **Cloud Build 구성 파일 위치**: `cloudbuild.yaml` (프로젝트 루트에 있음)

---

## 5단계: 치환 변수 (선택)

- **고급** 또는 **변수** 섹션을 펼친 뒤, 필요하면 다음 치환 변수 추가:
  - `_REGION` = `asia-northeast3`
  - `_REPO` = `smartnotam`
  - `_SERVICE` = `smartnotam3`
- `cloudbuild.yaml`에 기본값이 있으므로 비워 두어도 동작합니다. 다른 리전/저장소/서비스명을 쓰는 프로젝트일 때만 변경하면 됩니다.

---

## 6단계: 트리거 저장 및 테스트

1. **이름**: 예) `smartbrief-github-push`
2. **만들기** (또는 **저장**) 클릭
3. 트리거 목록에서 방금 만든 트리거 옆 **실행** 버튼으로 수동 실행해 보기 (선택)
   - 또는 로컬에서 `git push origin main` 한 번 하고, **Cloud Build** → **히스토리**에서 빌드가 시작되는지 확인

---

## 동작 흐름 요약

1. **이벤트**: `main` 브랜치에 push
2. **소스**: Cloud Build가 GitHub에서 해당 커밋 코드를 가져옴 (클론)
3. **구성**: 저장소 루트의 `cloudbuild.yaml` 실행
   - **Step 1**: `docker build`로 이미지 빌드 (Dockerfile 사용)
   - **Step 2**: 이미지를 Artifact Registry에 푸시  
     `{REGION}-docker.pkg.dev/{PROJECT_ID}/{REPO}/{SERVICE}:{SHORT_SHA}` 및 `:latest`
   - **Step 3**: `gcloud run deploy`로 Cloud Run 서비스 업데이트 (같은 이미지로 배포)
4. **결과**: 해당 프로젝트의 Cloud Run 서비스가 새 이미지로 자동 갱신됨

---

## 환경 변수 (GEMINI_API_KEY 등) 참고

- **첫 배포**는 `deploy_mac xxx.sh`로 해 두면, Cloud Run 서비스에 이미 **GEMINI_API_KEY**, **GOOGLE_MAPS_API_KEY** 등이 설정되어 있습니다.
- 트리거 배포는 **이미지만 교체**하고, 기존에 설정된 환경 변수는 그대로 유지됩니다.
- 새 환경 변수를 추가·변경하려면 GCP 콘솔 **Cloud Run** → 해당 서비스 → **수정 및 새 리비전 배포** → **변수 및 시크릿**에서 수정하거나, `cloudbuild.yaml`의 deploy 단계에 `--set-env-vars` 등을 추가해 구성할 수 있습니다.

---

## 문제 해결

- **권한 오류**: Cloud Build 서비스 계정에 Artifact Registry 쓰기, Cloud Run 배포 권한이 있어야 합니다. (이전에 `deploy_mac` 스크립트에서 역할 부여한 것과 동일한 프로젝트라면 보통 동작합니다.)
- **빌드 실패**: **Cloud Build** → **히스토리**에서 해당 빌드 클릭 → **로그**에서 단계별 에러 확인.
- **저장소 연결 끊김**: **Cloud Build** → **트리거**에서 연결을 다시 선택하거나, GitHub 앱/연결을 재설정.

이 순서대로 하면 GitHub에 push할 때마다 GCR(Artifact Registry)에 이미지가 올라가고, Cloud Run과 연동되어 자동 배포됩니다.
