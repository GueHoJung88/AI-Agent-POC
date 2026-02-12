#!/usr/bin/env bash
set -e

# ==========================================================
# START: Build and load images into *kpmg-poc* kind cluster
# ==========================================================

echo "== [0] docker build =="
docker build -t ai-core:local ./apps/ai-core
docker build -t bff:local ./apps/bff
docker build -t web-react:local ./apps/web-react
docker build -t web-flutter:local ./apps/web-flutter

echo "== [1] kind load into cluster: kpmg-poc (hard-coded) =="
kind load docker-image ai-core:local --name kpmg-poc
kind load docker-image bff:local --name kpmg-poc
kind load docker-image web-react:local --name kpmg-poc
kind load docker-image web-flutter:local --name kpmg-poc

echo "== [2] sanity check: current kubectl contexts =="
kubectl config get-contexts

echo "== done =="
# ==========================================================
# END
# ==========================================================
