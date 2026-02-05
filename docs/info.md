## AZURE SECRET INFO

AZURE_OPENAI_ENDPOINT : https://kpmg-aoai-poc.openai.azure.com/

AZURE_OPENAI_API_KEY : YOUR_AZURE_OPENAI_API_KEY

AZURE_OPENAI_DEPLOYMENT(배포 이름) : kpmg-aoai-poc

## 실행 순서

# 1) 클러스터 생성
bash scripts/kind-up.sh

# 2) ingress 설치
bash scripts/ingress-install.sh

# 3) 이미지 빌드 + kind 로드
bash scripts/build-load-kind.sh

# 4) 배포
bash scripts/deploy.sh

# 5) 접속
# 브라우저: http://kpmg-poc.local
# Flutter:   http://kpmg-poc.local/flutter
