.PHONY: help docker-build docker-push deploy

.DEFAULT_GOAL := help

DOCKERHUB_USERNAME ?= your-dockerhub-username
AI_IMAGE ?= $(DOCKERHUB_USERNAME)/dbaas-ai:latest

help: 
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

docker-build:
	@echo "Building Docker image: $(AI_IMAGE)"
	DOCKER_BUILDKIT=1 docker build -t $(AI_IMAGE) .

docker-push: docker-build 
	docker push $(AI_IMAGE)

deploy: 
	@if [ "$(AI_IMAGE)" = "your-dockerhub-username/dbaas-ai:latest" ]; then \
		echo "ERROR: Set DOCKERHUB_USERNAME or AI_IMAGE before deploying"; exit 1; fi
	@echo "Deploying AI service to Kubernetes..."
	kubectl apply -f deploy/postgres.yaml
	kubectl apply -f deploy/configmap.yaml
	kubectl apply -f deploy/secret.yaml
	AI_IMAGE=$(AI_IMAGE) envsubst < deploy/deployment.yaml | kubectl apply -f -
	kubectl apply -f deploy/service.yaml
	kubectl apply -f deploy/ingress.yaml
	@echo "Deploy complete. Check: kubectl get pods -n default -l app=ai-service"
