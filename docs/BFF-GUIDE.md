# BFF (Backend For Frontend) 가이드

## 개요
BFF는 Express.js 기반의 백엔드 포워드 프록시 서버입니다. 프론트엔드와 AI-Core 서버 사이의 중간 계층 역할을 합니다.

## 🎯 용도
- **API 프록시**: 프론트엔드의 모든 요청을 AI-Core로 포워드
- **CORS 처리**: 브라우저 보안 정책 관리
- **헬스 체크**: 서버 상태 모니터링
- **로드 밸런싱**: 향후 확장 가능한 구조

## 📋 기술 스택
- **런타임**: Node.js 20 (Alpine)
- **프레임워크**: Express.js 4.19
- **프록시**: http-proxy-middleware 3.0
- **배포**: Docker + Kubernetes

## 📂 프로젝트 구조

```
apps/bff/
├── package.json          # 의존성 및 스크립트
├── src/
│   └── server.js         # Express 서버 로직
└── Dockerfile            # Docker 빌드 설정
```

## 🚀 사용 방법

### 1. 로컬 개발 환경

**의존성 설치:**
```bash
cd apps/bff
npm install
```

**서버 시작:**
```bash
npm start
```

또는

```bash
node src/server.js
```

**기본 포트**: 3000

**헬스 체크:**
```bash
curl http://localhost:3000/health
```

응답 예시:
```json
{
  "ok": true,
  "aiCore": "http://localhost:8000"
}
```

### 2. 환경 변수

**AI-Core 연결 주소 설정:**
```bash
export AI_CORE_URL=http://ai-core:8000
node src/server.js
```

**기본값**: `http://localhost:8000` (로컬 개발용)

## 🔄 API 라우팅

### 요청 흐름
```
프론트엔드
  ↓
BFF (:3000)
  ↓ HTTP Proxy
AI-Core (:8000)
```

### 지원 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 서버 상태 확인 |
| `/api/*` | POST | AI-Core 요청 프록시 |

### 프록시 규칙
```javascript
// /api/chat → /chat (AI-Core)
// /api/report → /report
// /api/feedback → /feedback
```

**예시 요청:**
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"테스트","top_k":8}'
```

## 📦 Docker 배포

### 이미지 빌드
```bash
docker build -t bff:local ./apps/bff
```

### 로컬 실행
```bash
docker run -p 3000:3000 \
  -e AI_CORE_URL=http://host.docker.internal:8000 \
  bff:local
```

### 환경 변수 설정
```bash
docker run -p 3000:3000 \
  -e AI_CORE_URL=http://ai-core:9000 \
  bff:local
```

## 🐳 Kubernetes 배포

### 배포 파일: `deploy/k8s/base/bff.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bff
  namespace: kpmg-poc
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bff
  template:
    metadata:
      labels:
        app: bff
    spec:
      containers:
        - name: bff
          image: bff:local
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 3000
          env:
            - name: AI_CORE_URL
              value: "http://ai-core:9000"
---
apiVersion: v1
kind: Service
metadata:
  name: bff
  namespace: kpmg-poc
spec:
  selector:
    app: bff
  ports:
    - port: 3000
      targetPort: 3000
```

### 배포 명령
```bash
kubectl apply -f deploy/k8s/base/bff.yaml
kubectl -n kpmg-poc get pods
kubectl -n kpmg-poc logs -f deployment/bff
```

## 📝 코드 구조

### server.js
```javascript
import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";

const app = express();
app.use(express.json({ limit: "2mb" }));

const AI_CORE_URL = process.env.AI_CORE_URL || "http://localhost:8000";

// 헬스 체크
app.get("/health", (_, res) => res.json({ ok: true, aiCore: AI_CORE_URL }));

// API 프록시
app.use(
  "/api",
  createProxyMiddleware({
    target: AI_CORE_URL,
    changeOrigin: true,
    pathRewrite: { "^/api": "" }, // /api/chat -> /chat
  })
);

app.listen(3000, () => console.log("BFF listening on :3000"));
```

## 🔧 설정 커스터마이징

### 요청 크기 제한 변경
```javascript
app.use(express.json({ limit: "5mb" })); // 기본: 2mb
```

### 로깅 추가
```javascript
const createProxyMiddleware = (options) => {
  return (req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    next();
  };
};
```

### 요청/응답 헤더 수정
```javascript
createProxyMiddleware({
  target: AI_CORE_URL,
  changeOrigin: true,
  onProxyReq: (proxyReq, req, res) => {
    proxyReq.setHeader("X-Forwarded-For", req.ip);
  },
})
```

## ⚠️ 주의사항

### 1. AI-Core 연결 실패
**증상**: 응답이 502 Bad Gateway
**해결**:
- AI-Core 서버 실행 확인: `curl http://localhost:8000/health`
- `AI_CORE_URL` 환경 변수 확인
- 네트워크 연결 확인

### 2. CORS 에러
현재 설정에서는 `changeOrigin: true`로 CORS 처리됨.
추가 헤더 필요 시:
```javascript
onProxyReq: (proxyReq) => {
  proxyReq.setHeader("Access-Control-Allow-Origin", "*");
}
```

### 3. 포트 충돌
```bash
# 포트 3000 사용 중인 프로세스 찾기
lsof -i :3000

# 다른 포트로 실행
PORT=3001 npm start
```

## 📊 모니터링

### 로그 확인
```bash
# 로컬
npm start

# Kubernetes
kubectl -n kpmg-poc logs -f deployment/bff
```

### 메트릭 수집 (향후 구현)
Prometheus 연동 가능한 구조:
```javascript
app.get("/metrics", (_, res) => {
  res.send(`# HELP bff_requests_total Total requests
# TYPE bff_requests_total counter
bff_requests_total{method="POST",path="/api/chat"} 42
`);
});
```

## 📚 참고 자료
- [Express.js 문서](https://expressjs.com/)
- [http-proxy-middleware](https://github.com/chimurai/http-proxy-middleware)
- [Node.js 공식 문서](https://nodejs.org/en/docs/)
