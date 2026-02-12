#!/usr/bin/env bash
set -e

# ==========================================================
# START: Hard-coded context to prevent accidental deploy
# ==========================================================
# ✅ 항상 kpmg-poc 클러스터로만 배포되도록 고정
kubectl --context kind-kpmg-poc apply -f deploy/k8s/base/namespace.yaml
kubectl --context kind-kpmg-poc apply -f deploy/k8s/overlays/local/secret.yaml
kubectl --context kind-kpmg-poc apply -f deploy/k8s/base/ai-core.yaml
kubectl --context kind-kpmg-poc apply -f deploy/k8s/base/bff.yaml
kubectl --context kind-kpmg-poc apply -f deploy/k8s/base/web-react.yaml
kubectl --context kind-kpmg-poc apply -f deploy/k8s/base/web-flutter.yaml
kubectl --context kind-kpmg-poc apply -f deploy/k8s/ingress-nginx/ingress.yaml

# ✅ Secret(envFrom) 변경은 파드가 자동으로 env를 다시 읽지 않음 → 롤링 재시작 필수
kubectl --context kind-kpmg-poc -n kpmg-poc rollout restart deploy/ai-core deploy/bff deploy/web-react deploy/web-flutter

echo "[deploy] show pods in kpmg-poc..."
kubectl --context kind-kpmg-poc -n kpmg-poc get pods -o wide

echo "[deploy] show ingress-nginx controller pods..."
kubectl --context kind-kpmg-poc -n ingress-nginx get pods -o wide

echo "[deploy] done."
# ==========================================================
# END: Hard-coded context
# ==========================================================kubectl --context kind-kpmg-poc -n kpmg-poc get pods
