# Vite Dev Server 개발 가이드

## 개요
Vite는 빠른 개발 서버와 빌드 도구입니다. React 프론트엔드 개발을 로컬에서 테스트할 때 사용됩니다.

## 🎯 용도
- **Hot Module Replacement (HMR)**: 파일 수정 시 자동으로 브라우저에 반영
- **빠른 개발 경험**: Esbuild 기반 번들링으로 빠른 시작 및 재빌드
- **타입스크립트 지원**: TypeScript 자동 변환
- **정적 자산 처리**: CSS, 이미지 등 자동 최적화

## 📋 준비 사항

### 1. 의존성 설치
```bash
cd apps/web-react
npm install
```

**설치되는 주요 패키지:**
- `vite`: 빌드 도구
- `react`: UI 라이브러리
- `@vitejs/plugin-react`: React JSX 변환
- `typescript`: 타입 체크

### 2. 프로젝트 구조
```
apps/web-react/
├── package.json           # 의존성 및 스크립트
├── vite.config.ts         # Vite 설정
├── tsconfig.json          # TypeScript 설정
├── index.html             # 엔트리포인트
└── src/
    ├── main.tsx           # React DOM 렌더링
    ├── App.tsx            # 메인 컴포넌트
    └── lib/
        └── api.ts         # API 통신 헬퍼
```

## 🚀 사용 방법

### 개발 서버 시작
```bash
cd apps/web-react
npm run dev
```

**출력 예시:**
```
  VITE v5.4.21  ready in 301 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.0.46:5173/
```

### 브라우저에서 접속
- **로컬**: http://localhost:5173/
- **네트워크**: http://192.168.0.46:5173/ (또는 표시된 IP)

### 터미널 단축키
| 단축키 | 기능 |
|--------|------|
| `r` + Enter | 서버 재시작 |
| `u` + Enter | 서버 URL 표시 |
| `o` + Enter | 브라우저 자동 열기 |
| `c` + Enter | 콘솔 정리 |
| `q` + Enter | 서버 종료 |

## 📝 개발 기능

### Copilot Chat (RAG)
```
1. 질문 입력 필드에 질문 입력
2. "Ask" 버튼 클릭
3. AI 응답 및 근거(Citations) 확인
4. "👍 Feedback" 버튼으로 피드백 제출
```

**API 엔드포인트:**
- POST `/api/chat`: 질문 처리
- POST `/api/feedback`: 사용자 피드백 기록

### Agent: 보고서 생성
```
1. 시나리오 입력 필드에 작업 내용 입력
2. "Generate Report" 버튼 클릭
3. JSON 형식의 보고서 출력 확인
```

**API 엔드포인트:**
- POST `/api/report`: 보고서 생성 (조사 → 요약 → 작성)

## 🔧 설정 파일

### vite.config.ts
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});
```

### tsconfig.json
TypeScript 컴파일 설정. React JSX 자동 변환 포함.

## ⚠️ 주의사항

### 1. BFF 서버 필수
Vite dev server만으로는 API 요청이 작동하지 않습니다.
BFF(Backend For Frontend) 서버도 실행해야 합니다.

```bash
# 별도 터미널에서
cd apps/bff
npm install
npm start
```

### 2. API 프록시 (개발 시)
현재 코드는 `/api` 경로로 요청하며, BFF가 이를 AI-Core로 프록시합니다.
- Vite: http://localhost:5173
- BFF: http://localhost:3000
- AI-Core: http://localhost:8000

### 3. 빌드 전 테스트
```bash
npm run build
```

결과물: `dist/` 폴더에 최적화된 정적 파일 생성

## 🐛 문제 해결

### "Cannot find module" 에러
```bash
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### 포트 이미 사용 중
```bash
# 포트 5173 사용 중인 프로세스 확인
lsof -i :5173

# 다른 포트로 실행
npm run dev -- --port 5174
```

### Hot Reload 작동 안 함
1. 파일이 제대로 저장되었는지 확인
2. 브라우저 DevTools 확인 (콘솔 에러)
3. 서버 재시작 (`r` + Enter)

## 📚 참고 자료
- [Vite 공식 문서](https://vitejs.dev/)
- [React 공식 문서](https://react.dev/)
- [TypeScript 핸드북](https://www.typescriptlang.org/docs/)
