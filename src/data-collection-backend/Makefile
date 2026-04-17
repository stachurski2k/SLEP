
# Variables - Default to 'statistics' if no app is specified
IMAGE_NAME = data-collection-backend
PORT ?= 5000

.PHONY: help sync run docker-build docker-run

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

sync: ## Install dependencies for the specific app (e.g., make install APP=live)
	uv sync

run: ## Run uv app
	uv run app.main.py

docker-build: ## Build the Docker image for the app
	sudo docker build -t $(IMAGE_NAME) .

docker-run: ## Run the app in a container 
	sudo docker run -p $(PORT):5000 $(IMAGE_NAME) 
