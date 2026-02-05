#!/usr/bin/env bash
set -euo pipefail

KIND_MANIFEST="https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml"

is_kind() {
  kubectl get nodes -o name | grep -qi kind && return 0
  kubectl config current-context | grep -qi kind && return 0
  return 1
}

echo "[*] Removing existing ingress-nginx namespace (if any)..."
kubectl delete ns ingress-nginx --wait=true >/dev/null 2>&1 || true

if is_kind; then
  echo "[*] Detected kind. Installing ingress-nginx via provider/kind manifest..."
  kubectl apply -f "${KIND_MANIFEST}"
  kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=180s
  echo "✅ ingress-nginx ready (kind provider)"
else
  echo "[*] Non-kind cluster. Installing ingress-nginx via Helm..."
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
  helm repo update
  helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx --create-namespace
  kubectl -n ingress-nginx rollout status deployment/ingress-nginx-controller
  echo "✅ ingress-nginx ready (helm)"
fi
