# Variables - Default to 'statistics' if no app is specified
.PHONY: help run run-dev

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build:
	docker compose build

run: 
	docker compose up s3 data-collection-api data-collection-worker data-collection-flower postgres redis -d

run-dev: 
	docker compose up s3-dev data-collection-api data-collection-worker data-collection-flower postgres redis -d

