# 프로젝트 아키텍처 및 기술 스택

## 📐 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                      브라우저 (사용자)                           │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP/HTTPS
                                 ▼
                    ┌─────────────────────────┐
                    │   Nginx Ingress         │
                    │  (kpmg-poc.local)       │
                    │  - 포트 80/443 매핑     │
                    └──┬──────────┬──────┬────┘
                       │          │      │
        ┌──────────────┴──┐  ┌────┴──┐  └─────┐
        │                 │  │       │        │
        ▼                 ▼  ▼       ▼        ▼
    (/) Web-React    (/api) BFF (/flutter) Web-Flutter
        │                 │       │
        ├─React UI        ├─Express.js        ├─Nginx
        │                 │ Proxy              │
        └─Vite Dev        │ Middleware         └─Flutter
                          │                      Placeholder
                          ▼
                    AI-Core (FastAPI)
                    ┌──────────────────┐
                    │ FastAPI :8000    │
                    ├──────────────────┤
                    │ • /chat          │
                    │ • /report        │
                    │ • /feedback      │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
    ┌────────────┐    ┌──────────────┐    ┌────────────┐
    │ Embeddings │    │ LLM Azure    │    │ Database   │
    │ (Offline)  │    │ OpenAI       │    │ PostgreSQL │
    │ Model      │    │              │    │ + pgvector │
    │ Download   │    │ Deployment:  │    │            │
    │            │    │ kpmg-aoai-poc│    │ RAG Chunks │
    └────────────┘    └──────────────┘    └────────────┘
```

## 🏗️ 계층별 설명

### 1️⃣ 프론트엔드 계층

#### Web-React (React + Vite)
```
기술:
- React 18.3.1 (UI)
- TypeScript 5.5.4 (타입 안전)
- Vite 5.4.2 (번들러)
@vitejs/plugin-react (JSX 변환)

구조:
src/
├── App.tsx           # 메인 컴포넌트 (Chat + Report)
├── main.tsx          # React DOM 진입점
└── lib/
    └── api.ts        # /api 프록시 호출

포트: 5173 (개발) / 80 (배포)
```

**기능:**
- Copilot Chat (RAG 질문 응답)
  - 질문 입력 → BFF API 호출
  - 응답 및 근거 표시
  - 피드백 제출

- Agent Report (보고서 생성)
  - 시나리오 입력 → 보고서 생성 API 호출
  - JSON 형식 결과 표시

#### Web-Flutter (Flutter Web)
```
기술:
- Flutter Web
- Nginx 서버

구조:
build/web/
└── index.html       # 현재 플레이스홀더

포트: 80
```

**상태:** 플레이스홀더 (실제 Flutter 빌드물 대기)

### 2️⃣ 백엔드 게이트웨이 계층

#### BFF (Backend For Frontend - Express.js)
```
기술:
- Node.js 20 (런타임)
- Express.js 4.19 (웹 프레임워크)
- http-proxy-middleware 3.0 (프록시)

구조:
src/server.js
├── GET /health          # 서버 상태
└── POST /api/*          # AI-Core 프록시

포트: 3000
```

**역할:**
- CORS 처리
- 요청 라우팅 (/api → AI-Core로 포워드)
- 요청 크기 제한 (2MB)
- 환경 변수 기반 동적 라우팅

**프록시 규칙:**
```
/api/chat       → AI-Core /chat
/api/report     → AI-Core /report
/api/feedback   → AI-Core /feedback
```

### 3️⃣ AI 코어 계층

#### AI-Core (FastAPI + RAG)
```
기술:
- Python 3.11 (언어)
- FastAPI 0.112.0 (웹 프레임워크)
- Pydantic 2.8.2 (데이터 검증)

구조:
src/
├── main.py              # FastAPI 라우트
├── agent.py             # RAG + LLM 통합
├── rag.py               # pgvector 검색
├── llm_azure.py         # Azure OpenAI 클라이언트
├── embeddings.py        # SentenceTransformer
├── db.py                # PostgreSQL 연결
├── schemas.py           # Pydantic 스키마
└── settings.py          # 환경 변수 설정

포트: 8000
```

**주요 API:**

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 서버 상태 |
| `/chat` | POST | 질문 처리 (RAG) |
| `/report` | POST | 보고서 생성 (Agent) |
| `/feedback` | POST | 사용자 피드백 기록 |

**Copilot Chat 흐름:**
```
1. 사용자 질문 수신
   ↓
2. 질문 임베딩 생성 (SentenceTransformer)
   ↓
3. 벡터 DB 검색 (pgvector, top_k 결과)
   ↓
4. 문맥 구성 (retrieved chunks)
   ↓
5. Azure OpenAI LLM 호출
   ↓
6. 응답 + 근거 반환
```

**Report Agent 흐름:**
```
1. 시나리오 입력
   ↓
2. 문서 그룹 자동 라우팅
   - 키워드 기반 카테고리 분류
   - LLM, 법률, 사례 등
   ↓
3. 시나리오 임베딩 + 검색
   ↓
4. JSON 보고서 생성 프롬프트
   - 조사(Research) 단계
   - 작성(Writer) 단계
   ↓
5. 검증 및 반환
```

### 4️⃣ 데이터 계층

#### PostgreSQL + pgvector
```
기술:
- PostgreSQL 15+ (데이터베이스)
- pgvector 0.3.2 (벡터 확장)

주요 테이블:
- rag_chunks
  ├── id (UUID)
  ├── content (TEXT)
  ├── embedding (vector)
  ├── doc_title (TEXT)
  ├── page (INT)
  ├── file_path (TEXT)
  ├── doc_group (TEXT)
  └── metadata (JSONB)

- rag_query_log
  ├── id (UUID)
  ├── trace_id (UUID)
  ├── user_id (TEXT)
  ├── question (TEXT)
  ├── answer (TEXT)
  ├── retrieved_meta (JSONB)
  └── timings (JSONB)

- rag_feedback
  ├── id (UUID)
  ├── query_log_id (UUID)
  ├── rating (INT)
  ├── comment (TEXT)
  └── metadata (JSONB)
```

**호스트:** 192.168.0.69:5432 (로컬 환경)

#### 외부 서비스

**Azure OpenAI:**
```
엔드포인트: https://kpmg-aoai-poc.openai.azure.com/
배포명: kpmg-aoai-poc
모델: GPT-3.5/4 (설정에 따라)
API 버전: 2024-06-01
```

**임베딩 모델:**
```
로컬: BAAI/bge-small-en-v1.5 (기본)
또는: sentence-transformers/all-MiniLM-L6-v2
다운로드: Hugging Face에서 자동
```

## 🔄 요청 흐름

### Copilot Chat 요청 흐름
```
1. 사용자 입력 (React UI)
   ↓
2. POST /api/chat (Vite localhost:5173)
   ↓
3. BFF 프록시 받음 (localhost:3000)
   ↓
4. AI-Core로 포워드 (localhost:8000 또는 k8s svc)
   ↓
5. FastAPI /chat 처리
   ├─ 임베딩 생성
   ├─ pgvector 검색
   ├─ 문맥 구성
   ├─ Azure OpenAI 호출
   └─ 로깅
   ↓
6. 응답 반환 (question → answer, citations)
   ↓
7. 사용자에게 표시 (React UI)
```

### Report Agent 요청 흐름
```
1. 사용자 입력 (시나리오, React UI)
   ↓
2. POST /api/report (Vite localhost:5173)
   ↓
3. BFF 프록시 받음
   ↓
4. AI-Core /report 처리
   ├─ 문서 그룹 라우팅 (route_doc_group)
   ├─ 시나리오 임베딩
   ├─ pgvector 검색
   ├─ Azure OpenAI 보고서 생성
   │  {
   │    "summary": "...",
   │    "risks": [...],
   │    "requirements": [...],
   │    "recommended_actions": [...],
   │    "checklist": [...]
   │  }
   └─ 로깅
   ↓
5. JSON 보고서 반환
   ↓
6. 사용자에게 표시 (React UI)
```

## 🚀 배포 환경

### 로컬 개발
```
프론트엔드:  http://localhost:5173 (Vite Dev)
BFF:         http://localhost:3000
AI-Core:     http://localhost:8000
PostgreSQL:  192.168.0.69:5432
```

### Kubernetes (KinD)
```
Ingress:     http://kpmg-poc.local
├── / → web-react:80
├── /api/* → bff:3000
└── /flutter → web-flutter:80

내부 서비스:
- web-react.kpmg-poc.svc.cluster.local:80
- bff.kpmg-poc.svc.cluster.local:3000
- ai-core.kpmg-poc.svc.cluster.local:9000
- web-flutter.kpmg-poc.svc.cluster.local:80
```

## 📦 컨테이너 이미지

| 이미지 | Dockerfile | 기본 포트 | 크기 |
|--------|-----------|---------|------|
| `ai-core:local` | `apps/ai-core/Dockerfile` | 8000 | ~2GB |
| `bff:local` | `apps/bff/Dockerfile` | 3000 | ~150MB |
| `web-react:local` | `apps/web-react/Dockerfile` | 80 | ~50MB |
| `web-flutter:local` | `apps/web-flutter/Dockerfile` | 80 | ~50MB |

**빌드 명령:**
```bash
docker build -t ai-core:local ./apps/ai-core
docker build -t bff:local ./apps/bff
docker build -t web-react:local ./apps/web-react
docker build -t web-flutter:local ./apps/web-flutter
```

## 🔐 보안 및 환경 변수

### 민감한 정보 관리
```
deploy/k8s/overlays/local/secret.yaml
├── DATABASE_*               # DB 자격증명
├── AZURE_OPENAI_*           # API 키
└── EMBEDDING_MODEL_NAME     # 모델 지정
```

**주의:** `secret.yaml`은 버전 관리에서 제외 필요
```bash
echo "deploy/k8s/overlays/local/secret.yaml" >> .gitignore
```

## 📊 성능 특성

### 응답 시간 (추정)
- **임베딩**: 100-500ms (로컬 모델)
- **벡터 검색**: 50-200ms (pgvector)
- **LLM 생성**: 1-5s (Azure OpenAI)
- **전체**: 2-7초

### 확장성
- **수평 확장**: KinD 레플리카 증가 가능
- **垂직 확장**: 리소스 제한 조정
- **캐싱**: 개발 예정

## 📚 참고 자료
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [React 공식 문서](https://react.dev/)
- [pgvector 문서](https://github.com/pgvector/pgvector)
- [Azure OpenAI](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Kubernetes 공식 문서](https://kubernetes.io/docs/)
