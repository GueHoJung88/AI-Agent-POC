#!/usr/bin/env bash
set -e
kubectl apply -f deploy/k8s/base/namespace.yaml
kubectl apply -f deploy/k8s/overlays/local/secret.yaml
kubectl apply -f deploy/k8s/base/ai-core.yaml
kubectl apply -f deploy/k8s/base/bff.yaml
kubectl apply -f deploy/k8s/base/web-react.yaml
kubectl apply -f deploy/k8s/base/web-flutter.yaml
kubectl apply -f deploy/k8s/ingress-nginx/ingress.yaml

kubectl -n kpmg-poc get pods
