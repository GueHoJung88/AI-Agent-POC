#!/usr/bin/env bash
set -euo pipefail

# 목적:
# - kind 환경에서는 ingress-nginx의 "provider/kind" 매니페스트로 설치(가장 안정적)
# - 기존 helm 설치/기타 설치가 남아있으면 제거 후 재설치
# - 이미 설치되어 있으면 idempotent 하게 적용

KIND_MANIFEST="https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml"

echo "[1/4] Detecting Kubernetes context..."
CTX="$(kubectl config current-context || true)"
echo "  - current-context: ${CTX}"

echo "[2/4] Removing existing ingress-nginx (if any)..."
# namespace가 있으면 삭제(helm 설치든 뭐든 한 번에 정리)
if kubectl get ns ingress-nginx >/dev/null 2>&1; then
  kubectl delete ns ingress-nginx --wait=true || true
fi

echo "[3/4] Installing ingress-nginx for kind..."
kubectl apply -f "${KIND_MANIFEST}"

echo "[4/4] Waiting for controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

echo "✅ ingress-nginx installed and ready (kind provider)."
