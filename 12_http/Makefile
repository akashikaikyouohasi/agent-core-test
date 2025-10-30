.PHONY: help init plan apply destroy output test clean

# Variables
TERRAFORM_DIR = terraform
WEBSOCKET_URL = $(shell cd $(TERRAFORM_DIR) && terraform output -raw websocket_url 2>/dev/null || echo "")

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

init: ## Initialize Terraform
	@echo "Initializing Terraform..."
	cd $(TERRAFORM_DIR) && terraform init

plan: ## Plan Terraform changes
	@echo "Planning Terraform changes..."
	cd $(TERRAFORM_DIR) && terraform plan

apply: ## Apply Terraform changes
	@echo "Applying Terraform changes..."
	cd $(TERRAFORM_DIR) && terraform apply
	@echo ""
	@echo "Deployment complete!"
	@echo "WebSocket URL: $(WEBSOCKET_URL)"

destroy: ## Destroy all resources
	@echo "Destroying all resources..."
	cd $(TERRAFORM_DIR) && terraform destroy

output: ## Show Terraform outputs
	@cd $(TERRAFORM_DIR) && terraform output

url: ## Show WebSocket URL
	@echo "WebSocket URL: $(WEBSOCKET_URL)"

test-echo: ## Test echo action
	@if [ -z "$(WEBSOCKET_URL)" ]; then \
		echo "Error: WebSocket URL not found. Deploy first with 'make apply'"; \
		exit 1; \
	fi
	@echo "Testing echo action..."
	@python3 websocket_client.py --url "$(WEBSOCKET_URL)" --action echo --data '{"message": "Hello WebSocket!"}'

test-uppercase: ## Test uppercase action
	@if [ -z "$(WEBSOCKET_URL)" ]; then \
		echo "Error: WebSocket URL not found. Deploy first with 'make apply'"; \
		exit 1; \
	fi
	@echo "Testing uppercase action..."
	@python3 websocket_client.py --url "$(WEBSOCKET_URL)" --action uppercase --data '{"text": "hello world"}'

test-reverse: ## Test reverse action
	@if [ -z "$(WEBSOCKET_URL)" ]; then \
		echo "Error: WebSocket URL not found. Deploy first with 'make apply'"; \
		exit 1; \
	fi
	@echo "Testing reverse action..."
	@python3 websocket_client.py --url "$(WEBSOCKET_URL)" --action reverse --data '{"text": "Hello WebSocket"}'

test-timestamp: ## Test timestamp action
	@if [ -z "$(WEBSOCKET_URL)" ]; then \
		echo "Error: WebSocket URL not found. Deploy first with 'make apply'"; \
		exit 1; \
	fi
	@echo "Testing timestamp action..."
	@python3 websocket_client.py --url "$(WEBSOCKET_URL)" --action timestamp --data '{}'

test-all: ## Run all tests
	@echo "Running all tests..."
	@make test-echo
	@echo ""
	@make test-uppercase
	@echo ""
	@make test-reverse
	@echo ""
	@make test-timestamp

logs-websocket: ## Tail WebSocket handler logs
	@echo "Tailing WebSocket handler logs..."
	aws logs tail /aws/lambda/websocket-lambda-websocket-handler --follow

logs-processor: ## Tail processor logs
	@echo "Tailing processor logs..."
	aws logs tail /aws/lambda/websocket-lambda-processor --follow

clean: ## Clean Terraform files
	@echo "Cleaning Terraform files..."
	rm -rf $(TERRAFORM_DIR)/.terraform
	rm -f $(TERRAFORM_DIR)/.terraform.lock.hcl
	rm -f $(TERRAFORM_DIR)/terraform.tfstate*
	rm -f $(TERRAFORM_DIR)/*.zip
	@echo "Clean complete!"

install-deps: ## Install Python dependencies for testing
	@echo "Installing Python dependencies..."
	pip3 install websockets

check-deps: ## Check if required dependencies are installed
	@echo "Checking dependencies..."
	@command -v terraform >/dev/null 2>&1 || { echo "Error: terraform is not installed"; exit 1; }
	@command -v aws >/dev/null 2>&1 || { echo "Error: aws cli is not installed"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is not installed"; exit 1; }
	@python3 -c "import websockets" 2>/dev/null || { echo "Warning: websockets library not installed. Run 'make install-deps'"; }
	@echo "All dependencies are installed!"
