# Variables - Default to 'statistics' if no app is specified
IMAGE_NAME = data-collection-frontend
PORT ?= 3000

.PHONY: help install dev build docker-build docker-run

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies for the specific app (e.g., make install APP=live)
	npm install

dev: ## Run the React dev server locally
	npm run dev

build: ## Build the production bundle (HTML/JS/CSS)
	npm run build

docker-build: ## Build the Docker image for the app
	sudo docker build -t $(IMAGE_NAME) .

docker-run: ## Run the app in a container 
	sudo docker run -p $(PORT):80 $(IMAGE_NAME) 
