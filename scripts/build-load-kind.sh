#!/usr/bin/env bash
set -e

# build images
docker build -t ai-core:local ./apps/ai-core
docker build -t bff:local ./apps/bff
docker build -t web-react:local ./apps/web-react
docker build -t web-flutter:local ./apps/web-flutter

# load to kind
kind load docker-image ai-core:local --name kpmg-poc
kind load docker-image bff:local --name kpmg-poc
kind load docker-image web-react:local --name kpmg-poc
kind load docker-image web-flutter:local --name kpmg-poc
