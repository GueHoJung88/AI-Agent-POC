# Kubernetes 배포 가이드

## 개요
이 프로젝트는 KinD(Kubernetes in Docker)를 사용하여 로컬 Kubernetes 환경에 배포됩니다.
Ingress를 통해 프론트엔드, 백엔드, API를 단일 진입점으로 관리합니다.

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────┐
│         Nginx Ingress (kpmg-poc.local)          │
├───────────────────┬─────────────────┬───────────┤
│                   │                 │           │
▼                   ▼                 ▼           ▼
/ (root)         /api/...         /flutter/...
  │
Web-React       BFF              Web-Flutter
  │              │                  │
  ▼              ▼                  ▼
:80            :3000              :80
(Pod)          (Pod)              (Pod)
                 │
                 ▼ Proxy
             AI-Core:8000
               (Pod)
                 │
                 ▼ Query
             PostgreSQL
             + pgvector
```

## 📋 사전 요구사항

### 설치 필요 도구
```bash
# KinD 설치
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin

# kubectl 설치
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin

# Helm 설치 (Ingress 설치용)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Docker 설치 (기존)
docker --version
```

## 🚀 배포 프로세스

### 1단계: 클러스터 생성
```bash
bash scripts/kind-up.sh
```

**수행 작업:**
- KinD 클러스터 생성 (이름: `kpmg-poc`)
- 포트 매핑 설정 (80, 443)
- kubeconfig 설정

**확인:**
```bash
kubectl cluster-info
kubectl get nodes
```

### 2단계: Ingress 설치
```bash
bash scripts/ingress-install.sh
```

**수행 작업:**
- Helm repo 추가
- ingress-nginx 설치
- 롤아웃 대기

**확인:**
```bash
kubectl -n ingress-nginx get pods
kubectl -n ingress-nginx get svc
```

### 3단계: Docker 이미지 빌드 및 로드
```bash
bash scripts/build-load-kind.sh
```

**수행 작업:**
- `ai-core:local` 빌드
- `bff:local` 빌드
- `web-react:local` 빌드
- `web-flutter:local` 빌드
- 이미지들을 KinD로 로드

**확인:**
```bash
kind load docker-image --help
docker images | grep local
```

### 4단계: 리소스 배포
```bash
bash scripts/deploy.sh
```

**수행 작업:**
1. Namespace 생성: `kpmg-poc`
2. Secrets 생성: AI-Core 환경 변수
3. Deployments 생성:
   - AI-Core (FastAPI)
   - BFF (Express)
   - Web-React (Nginx)
   - Web-Flutter (Nginx)
4. Services 생성: 각 애플리케이션 노출
5. Ingress 생성: 라우팅 규칙 설정

**확인:**
```bash
kubectl -n kpmg-poc get all
kubectl -n kpmg-poc logs -f deployment/ai-core
```

## 🌐 접속 및 테스트

### 호스트 파일 설정
```bash
# /etc/hosts에 추가
127.0.0.1 kpmg-poc.local
```

**Linux/Mac:**
```bash
echo "127.0.0.1 kpmg-poc.local" | sudo tee -a /etc/hosts
```

**Windows (관리자):**
```
C:\Windows\System32\drivers\etc\hosts에 추가
127.0.0.1 kpmg-poc.local
```

### 브라우저 접속
| URL | 설명 |
|-----|------|
| http://kpmg-poc.local | Web-React (메인 UI) |
| http://kpmg-poc.local/flutter | Web-Flutter |
| http://kpmg-poc.local/api/health | BFF 헬스 체크 |

### curl 테스트
```bash
# BFF 헬스 체크
curl http://kpmg-poc.local/api/health

# AI-Core 라우팅 테스트
curl -X POST http://kpmg-poc.local/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"테스트","top_k":8}'
```

## 📁 배포 파일 구조

```
deploy/k8s/
├── base/                           # 기본 리소스
│   ├── namespace.yaml             # kpmg-poc 네임스페이스
│   ├── ai-core.yaml              # AI-Core Deployment + Service
│   ├── bff.yaml                  # BFF Deployment + Service
│   ├── web-react.yaml            # Web-React Deployment + Service
│   ├── web-flutter.yaml          # Web-Flutter Deployment + Service
│   └── ingress.yaml              # Nginx Ingress 라우팅
└── overlays/local/               # 로컬 환경 커스터마이징
    ├── kind-config.yaml          # KinD 클러스터 설정
    └── secret.yaml               # 환경 변수 및 시크릿
```

## 🔐 Secrets 관리

### secret.yaml의 주요 환경 변수

**데이터베이스:**
```yaml
DATABASE_HOST: "192.168.0.69"       # PostgreSQL 호스트
DATABASE_PORT: "5432"
DATABASE_NAME: "ragdb"
DATABASE_USER: "raguser"
DATABASE_PASSWORD: "ragpassword"
```

**Azure OpenAI:**
```yaml
AZURE_OPENAI_ENDPOINT: "https://kpmg-aoai-poc.openai.azure.com/"
AZURE_OPENAI_API_KEY: "..."        # 실제 키로 변경 필요
AZURE_OPENAI_DEPLOYMENT: "kpmg-aoai-poc"
```

**임베딩 모델:**
```yaml
EMBEDDING_MODEL_NAME: "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_DOC_GROUP: "guide"
```

### Secret 업데이트
```bash
# 기존 secret 삭제
kubectl -n kpmg-poc delete secret ai-core-secrets

# 새 secret 생성
kubectl apply -f deploy/k8s/overlays/local/secret.yaml

# 포드 재시작 (새 환경 변수 로드)
kubectl -n kpmg-poc rollout restart deployment/ai-core
```

## 📊 상태 확인

### 포드 상태
```bash
# 모든 포드 확인
kubectl -n kpmg-poc get pods

# 특정 포드 상세 정보
kubectl -n kpmg-poc describe pod ai-core-xxx

# 로그 확인
kubectl -n kpmg-poc logs -f deployment/ai-core
```

### 서비스 상태
```bash
# 서비스 목록
kubectl -n kpmg-poc get svc

# 엔드포인트 확인
kubectl -n kpmg-poc get endpoints
```

### Ingress 상태
```bash
# Ingress 규칙 확인
kubectl -n kpmg-poc get ingress

# Ingress 상세 정보
kubectl -n kpmg-poc describe ingress kpmg-poc
```

## 🔄 업데이트 및 롤백

### 이미지 재빌드 및 배포
```bash
# 1. 이미지 재빌드
docker build -t ai-core:local ./apps/ai-core

# 2. KinD로 로드
kind load docker-image ai-core:local --name kpmg-poc

# 3. 포드 재시작
kubectl -n kpmg-poc rollout restart deployment/ai-core

# 4. 상태 확인
kubectl -n kpmg-poc rollout status deployment/ai-core
```

### 환경 변수 수정
```bash
# secret.yaml 수정 후
kubectl apply -f deploy/k8s/overlays/local/secret.yaml

# 포드 재시작
kubectl -n kpmg-poc rollout restart deployment/ai-core
```

### 이전 버전으로 롤백
```bash
# 롤아웃 히스토리 확인
kubectl -n kpmg-poc rollout history deployment/ai-core

# 이전 버전으로 롤백
kubectl -n kpmg-poc rollout undo deployment/ai-core
```

## ⚠️ 문제 해결

### 클러스터 삭제 및 재생성
```bash
# 기존 클러스터 삭제
kind delete cluster --name kpmg-poc

# 새 클러스터 생성
bash scripts/kind-up.sh
bash scripts/ingress-install.sh
bash scripts/build-load-kind.sh
bash scripts/deploy.sh
```

### 포드가 CrashLoopBackOff 상태
```bash
# 로그 확인
kubectl -n kpmg-poc logs <pod-name> --previous

# 환경 변수 확인
kubectl -n kpmg-poc get secret ai-core-secrets -o yaml

# Secret 업데이트
kubectl -n kpmg-poc delete secret ai-core-secrets
kubectl apply -f deploy/k8s/overlays/local/secret.yaml
```

### 이미지 풀 에러
```bash
# 이미지 재로드
kind load docker-image ai-core:local --name kpmg-poc
kind load docker-image bff:local --name kpmg-poc
kind load docker-image web-react:local --name kpmg-poc
kind load docker-image web-flutter:local --name kpmg-poc

# 포드 재시작
kubectl -n kpmg-poc delete pods --all
```

### 포트 이미 사용 중
```bash
# 포트 점유 프로세스 확인
lsof -i :80

# 다른 서비스 중지 또는 포트 변경
```

## 📈 스케일링

### 레플리카 수 증가
```bash
kubectl -n kpmg-poc scale deployment ai-core --replicas=3
kubectl -n kpmg-poc get pods
```

### 리소스 제한 설정
```yaml
# deployment에 추가
spec:
  containers:
  - name: ai-core
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "500m"
```

## 🧹 정리

### 전체 클러스터 삭제
```bash
kind delete cluster --name kpmg-poc
```

### 특정 리소스만 삭제
```bash
# 네임스페이스 삭제 (연쇄 삭제)
kubectl delete namespace kpmg-poc

# 개별 리소스 삭제
kubectl -n kpmg-poc delete deployment ai-core
kubectl -n kpmg-poc delete service ai-core
```

## 📚 참고 자료
- [KinD 공식 문서](https://kind.sigs.k8s.io/)
- [kubectl 명령어 리스트](https://kubernetes.io/docs/reference/kubectl/overview/)
- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Helm 공식 문서](https://helm.sh/docs/)
