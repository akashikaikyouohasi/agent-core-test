.PHONY: help setup install activate clean run-simple run-workflow test deploy logs

# 仮想環境のパス
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UV := uv

# デフォルトターゲット
help:
	@echo "利用可能なコマンド:"
	@echo "  make setup          - uv で仮想環境を作成"
	@echo "  make install        - 必要なパッケージをインストール"
	@echo "  make activate       - 仮想環境のアクティベート方法を表示"
	@echo "  make clean          - キャッシュと一時ファイルを削除"
	@echo "  make run-simple     - シンプルなワークフローを実行"
	@echo "  make run-workflow   - 複雑なワークフローを実行"
	@echo "  make test           - テストを実行"
	@echo "  make deploy         - AgentCoreにデプロイ"
	@echo "  make logs           - ログを表示"

# uv で仮想環境を作成
setup:
	@echo "uv venv [NAME]で仮想環境を作成中..."
	$(UV) venv $(VENV)
	@echo "✅ 仮想環境が作成されました: $(VENV)"
	@echo ""
	@echo "次のコマンドで仮想環境をアクティベートしてください:"
	@echo "  source $(VENV)/bin/activate"
	@echo ""
	@echo "その後、以下を実行してパッケージをインストール:"
	@echo "  make install"

# パッケージのインストール（仮想環境が必要）
install:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ 仮想環境が見つかりません。まず 'make setup' を実行してください"; \
		exit 1; \
	fi
	@echo "uv pip install [パッケージ名] でパッケージをインストール中..."
	$(UV) pip install -r requirements.txt
	@echo "✅ インストール完了"

# 仮想環境のアクティベート方法を表示
activate:
	@echo "仮想環境をアクティベート"
	source .venv/bin/activate

# キャッシュと一時ファイルの削除
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

# シンプルなワークフローを実行
run-simple:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ 仮想環境が見つかりません。'make setup' と 'make install' を実行してください"; \
		exit 1; \
	fi
	$(PYTHON) simple_workflow.py

# 複雑なワークフローを実行
run-workflow:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ 仮想環境が見つかりません。'make setup' と 'make install' を実行してください"; \
		exit 1; \
	fi
	$(PYTHON) workflow_example.py

# テストを実行
test:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ 仮想環境が見つかりません。'make setup' と 'make install' を実行してください"; \
		exit 1; \
	fi
	$(PYTHON) -m pytest tests/ -v

# AgentCoreにデプロイ
deploy:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ 仮想環境が見つかりません。'make setup' と 'make install' を実行してください"; \
		exit 1; \
	fi
	@echo "AgentCoreへのデプロイを開始..."
	$(PYTHON) deploy_workflow.py

# ログを表示
logs:
	tail -f *.log 2>/dev/null || echo "ログファイルが見つかりません"
