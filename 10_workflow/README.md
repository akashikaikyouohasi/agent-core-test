# Bedrock AgentCore Workflow 実験

このディレクトリでは Bedrock AgentCore のワークフロー機能を試します。

## セットアップ

```bash
# 依存パッケージのインストール
make install

# または
pip install -r requirements.txt
```

## 使い方

### 1. シンプルなワークフロー

```bash
make run-simple
```

2つのステップを持つ基本的なワークフローを実行します。

### 2. カスタマーサポートワークフロー

```bash
make run-workflow
```

問い合わせの分類、ルーティング、回答生成を行う実践的なワークフローを実行します。

## ワークフローの構造

### SimpleWorkflow
- **Step 1**: データの受け取りと処理
- **Step 2**: データの変換と最終出力

### CustomerSupportWorkflow
- **Step 1 (classify)**: 問い合わせの分類
- **Step 2 (route)**: 適切な担当者へのルーティング
- **Step 3 (respond)**: AIエージェントによる回答生成

## ファイル構成

```
10_workflow/
├── Makefile                 # タスク管理
├── requirements.txt         # Python依存パッケージ
├── simple_workflow.py       # シンプルなワークフロー例
├── workflow_example.py      # 複雑なワークフロー例
└── README.md               # このファイル
```

## その他のコマンド

```bash
# キャッシュと一時ファイルの削除
make clean

# ヘルプを表示
make help
```

## 環境変数

`.env` ファイルに以下を設定してください：

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_DEFAULT_REGION=us-east-1
```
