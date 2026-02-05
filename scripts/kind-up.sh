#!/usr/bin/env bash
set -e
kind create cluster --name kpmg-poc --config deploy/k8s/overlays/local/kind-config.yaml
kubectl cluster-info --context kind-kpmg-poc
