.PHONY: help setup install activate clean run-simple run-workflow test deploy logs

# 仮想環境のパス
VENV := .venv
PYTHON := $(VENV)/bin/python
AGENTCORE := $(VENV)/bin/agentcore
PIP := $(VENV)/bin/pip
UV := uv

# エントリーポイント
ENTRYPOINT := agents.py
# AWS
REGION := ap-northeast-1

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
	@echo "仮想環境をアクティベートするには:"
	@echo "  source $(VENV)/bin/activate"
	@echo ""
	@echo "非アクティベートするには:"
	@echo "  deactivate"

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

# ログを表示
logs:
	tail -f *.log 2>/dev/null || echo "ログファイルが見つかりません"

check-venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ 仮想環境が見つかりません。'make setup' と 'make install' を実行してください"; \
		exit 1; \
	fi

# AgentCoreのセットアップ
agentcore-setup: check-venv
	@echo "AgentCoreのセットアップを開始..."
	${AGENTCORE} configure --entrypoint $(ENTRYPOINT) --region $(REGION) --name stream_agent

# ローカルサーバーを起動（フォアグラウンド）
agentcore-local: check-venv
	@echo "AgentCoreのローカル起動を開始..."
	@echo "⚠️  Ctrl+C で停止できます"
	@echo "⚠️  別のターミナルで 'make agentcore-local-test' を実行してテストしてください"
	${AGENTCORE} launch --local --env OTEL_SDK_DISABLED=true

agentcore-local-test: check-venv
	@echo "📡 ローカルサーバー(localhost:8080)の接続を確認中..."
	@if curl -s http://localhost:8080/health > /dev/null 2>&1 || nc -z localhost 8080 > /dev/null 2>&1; then \
		echo "✅ ローカルサーバーが起動しています"; \
	else \
		echo "❌ ローカルサーバーが起動していません"; \
		echo ""; \
		echo "別のターミナルで以下を実行してサーバーを起動してください:"; \
		echo "  make agentcore-local"; \
		exit 1; \
	fi
	@echo "AgentCoreのローカルテストを開始..."
	@echo ""
	@echo "⏱️  テスト1: １たす１は２になる理由を千文字で解説して"
	@date +"%Y-%m-%d %H:%M:%S"
	@START=$$(date +%s); \
	${AGENTCORE} invoke --local '{"prompt": "１たす１は２になる理由を千文字で解説して"}'; \
	END=$$(date +%s); \
	DURATION=$$((END - START)); \
	echo ""; \
	echo "⏱️  実行時間: $${DURATION}秒"
#	@echo ""
#	@echo "⏱️  テスト2: 私が今いる場所の天気は？"
#	@START=$$(date +%s); \
#	${AGENTCORE} invoke --local '{"prompt": "私が今いる場所の天気は？"}'; \
#	END=$$(date +%s); \
#	DURATION=$$((END - START)); \
#	echo ""; \
#	echo "⏱️  実行時間: $${DURATION}秒"

agentcore-deploy: check-venv
	@echo "AgentCoreへのデプロイを開始..."
	agent${AGENTCORE}core launch

agentcore-status: check-venv
	@echo "AgentCoreのステータスを表示..."
	${AGENTCORE} status
agentcore-invoke-test: check-venv
	@echo "AgentCoreへのリクエストを送信..."
	${AGENTCORE} invoke '{"prompt": "１たす１は？"}'
	${AGENTCORE} invoke '{"prompt": "私が今いる場所の天気は？"}'
agentcore-invoke-test-workflow: check-venv
	@echo "AgentCoreへのworkflowリクエストを送信..."
	${AGENTCORE} invoke '{"prompt": "四半期のレポートを生成してください。"}'
