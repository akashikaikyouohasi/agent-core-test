# Lambdaコールドスタート完全回避アーキテクチャ

## 目標

- ✅ Lambdaのコールドスタートを完全に0にする
- ✅ プロビジョニング済み同時実行（Provisioned Concurrency）は使わない
- ✅ 低コストを維持
- ✅ AWS SigV4認証とWebSocket双方向通信を実現

---

## 🎯 解決策: ECS Fargate + Application Load Balancer + WebSocketサーバー

### アーキテクチャ

```
Client (WebSocket)
    ↓
Application Load Balancer (ALB)
    ↓
ECS Fargate (常駐プロセス)
    ├─ WebSocketサーバー（Node.js/Python）
    ├─ SigV4署名生成
    └─ AgentCore Runtime呼び出し
```

### メリット

✅ **コールドスタート完全ゼロ**
   - ECS Fargateは常駐プロセス
   - アプリケーションが常にメモリ上で待機

✅ **柔軟なスケーリング**
   - Auto Scaling設定可能
   - 最小タスク数1でもコールドスタートなし

✅ **WebSocketネイティブサポート**
   - ALBがWebSocket接続を直接サポート
   - API Gatewayの制約なし

✅ **長時間接続可能**
   - API Gateway WebSocketの制限（2時間）を超える接続が可能
   - AgentCoreの8時間実行にも対応

### デメリット

❌ **コストが高い**
   - Fargate: 最小構成で約 $15-30/月
   - ALB: 約 $16/月（固定）
   - **合計: 約$31-46/月**（Lambda $0.85/月と比較）

❌ **運用が複雑**
   - Dockerイメージのビルドとデプロイ
   - ECSタスク管理
   - ヘルスチェック設定

❌ **スケーリングに時間がかかる**
   - 新しいタスク起動: 30-60秒
   - Lambda（SnapStart除く）: 数秒

---

## 🚀 解決策2: Lambda SnapStart（Java/Python 3.13）

### アーキテクチャ

```
Client (WebSocket)
    ↓
API Gateway WebSocket
    ↓
Lambda (SnapStart有効)  ← コールドスタートほぼゼロ
    ├─ 初期化済みスナップショットから起動
    ├─ SigV4署名生成
    └─ AgentCore Runtime呼び出し
```

### Lambda SnapStartとは

AWS Lambda SnapStartは、関数の初期化フェーズのスナップショットを作成し、それを再利用することでコールドスタートを劇的に削減する機能です。

**対応ランタイム:**
- ✅ Java 11, 17, 21
- ✅ **Python 3.13**（2024年12月プレビュー）← これが使える！
- ❌ Python 3.11, 3.12（現在非対応）
- ❌ Node.js（非対応）

### コールドスタート時間比較

| ランタイム | 通常 | SnapStart有効 | 改善率 |
|-----------|------|--------------|--------|
| Python 3.11 | 200-500ms | - | - |
| Python 3.13 | 200-500ms | **50-100ms** | **80-90%削減** |
| Java 11 | 1-3秒 | **200ms以下** | **90%以上削減** |

### 実装方法

#### 1. Python 3.13に移行

**現在:**
```hcl
# terraform/main.tf
resource "aws_lambda_function" "websocket_handler" {
  runtime = "python3.11"
}
```

**変更後:**
```hcl
# terraform/main.tf
resource "aws_lambda_function" "websocket_handler" {
  runtime = "python3.13"  # SnapStart対応
  
  snap_start {
    apply_on = "PublishedVersions"
  }
}
```

#### 2. Lambda関数のバージョン管理

SnapStartは公開されたバージョンでのみ動作するため、エイリアスを使用：

```hcl
resource "aws_lambda_function" "websocket_handler" {
  # ... 省略 ...
  
  snap_start {
    apply_on = "PublishedVersions"
  }
  
  publish = true  # 自動的にバージョンを公開
}

# Lambdaエイリアス（常に最新バージョンを指す）
resource "aws_lambda_alias" "websocket_handler_live" {
  name             = "live"
  function_name    = aws_lambda_function.websocket_handler.function_name
  function_version = aws_lambda_function.websocket_handler.version
}

# API GatewayからはエイリアスのARNを参照
resource "aws_apigatewayv2_integration" "default" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_alias.websocket_handler_live.invoke_arn
}
```

### メリット

✅ **コールドスタートほぼゼロ**
   - 200-500ms → 50-100ms（80-90%削減）
   - 体感的にはほぼ感じられないレベル

✅ **追加コストなし**
   - SnapStartは無料機能
   - Lambda料金は通常と同じ

✅ **実装が簡単**
   - Terraform設定の追加のみ
   - アプリケーションコードの変更不要

✅ **既存アーキテクチャを維持**
   - API Gateway WebSocket + Lambda構成そのまま
   - 移行リスクが低い

### デメリット

⚠️ **Python 3.13はプレビュー版（2024年12月時点）**
   - 本番環境での使用は慎重に
   - GA（一般提供）まで待つ必要がある可能性

⚠️ **現在のPython 3.11からの移行が必要**
   - 互換性の確認が必要
   - ライブラリの対応状況を確認

---

## 🌐 解決策3: CloudFront Functions + Lambda@Edge

### アーキテクチャ

```
Client (WebSocket)
    ↓
CloudFront (WebSocket対応)
    ↓
Lambda@Edge (エッジロケーションで実行)  ← コールドスタート削減
    ↓
AgentCore Runtime
```

### 問題点

❌ **CloudFrontはWebSocketを直接サポートしていない**
   - HTTP/HTTPSのみ
   - WebSocketはOrigin（バックエンド）にパススルーするのみ

❌ **Lambda@EdgeはWebSocket統合に制約がある**
   - Viewer Request/Responseイベントのみ
   - WebSocketの双方向通信には不向き

**結論:** この方式は不適切

---

## ⚡ 解決策4: API Gateway REST API + Server-Sent Events (SSE)

### 結論: **不可能**

API Gateway REST APIは**Server-Sent Events（SSE）に対応していません**。

### 技術的な理由

❌ **統合タイムアウト: 最大29秒**
   - SSEは数分〜数時間の長時間接続を前提
   - API Gateway REST APIの統合タイムアウト: 50ms〜29秒
   - AgentCoreの処理時間（数秒〜数分）に対応不可

❌ **ストリーミングレスポンス非対応**
   - API Gateway REST APIはレスポンスをバッファリング
   - チャンク化レスポンス（Transfer-Encoding: chunked）非対応
   - `text/event-stream`形式のストリーミング不可

❌ **Lambda統合の制限**
   - Lambdaからのストリーミングレスポンスが返せない
   - レスポンス全体が揃うまで待機してから一括返送

### 参考: AWS公式ドキュメント

> Integration timeout for Regional APIs: 50 milliseconds - 29 seconds for all integration types, including Lambda, Lambda proxy, HTTP, HTTP proxy, and AWS integrations.

出典: [Quotas for configuring and running a REST API in API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html)

**結論:** API Gateway REST APIではSSE不可。WebSocket APIを使用するのが正解。

---

## 🎯 最終推奨アーキテクチャ

### Option A: Lambda SnapStart（推奨度: ⭐⭐⭐⭐⭐）

**待つべき理由:**
- Python 3.13のGA（一般提供）を待つ（おそらく2025年Q1-Q2）
- コスト増なし、実装簡単、効果絶大

**実装タイミング:**
```
NOW: Python 3.11で運用継続
  ↓
2025 Q1-Q2: Python 3.13 GA後に移行
  ↓
SnapStart有効化 → コールドスタート80-90%削減
```

**移行手順:**
1. Python 3.13のGA待ち
2. ローカルでPython 3.13互換性テスト
3. Terraform設定更新（`snap_start`ブロック追加）
4. デプロイ

### Option B: ECS Fargate（推奨度: ⭐⭐⭐）

**こんな場合に検討:**
- ✅ コストよりもパフォーマンス優先
- ✅ 高トラフィック（月100万リクエスト以上）
- ✅ WebSocket接続を2時間以上保持したい
- ✅ Dockerコンテナ運用の経験がある

**コスト試算:**
- Fargate (0.25 vCPU, 0.5 GB): ~$15/月
- ALB: ~$16/月
- データ転送: ~$5/月
- **合計: ~$36/月**

### Option C: 現状維持 + 最適化（推奨度: ⭐⭐⭐⭐）

**今すぐできること:**

1. **Lambda関数の最適化**
   ```python
   # グローバルスコープで初期化（再利用される）
   import boto3
   
   # Lambda起動時に1回だけ実行
   bedrock_client = boto3.client('bedrock-agentcore')
   apigw_client = boto3.client('apigatewaymanagementapi')
   
   def lambda_handler(event, context):
       # ここではクライアントを初期化しない
       pass
   ```

2. **メモリサイズの最適化**
   ```hcl
   resource "aws_lambda_function" "websocket_handler" {
     memory_size = 256  # 128 → 256に増やすとCPUも増えて初期化が速くなる
   }
   ```
   - メモリを増やすとCPUも比例して増える
   - 初期化時間が短縮される
   - コストは増えるが、実行時間が短くなるので相殺される可能性

3. **Lambda関数のウォームアップ（無料枠内）**
   ```hcl
   # EventBridge Ruleで5分ごとにping
   resource "aws_cloudwatch_event_rule" "lambda_warmer" {
     name                = "lambda-warmer"
     schedule_expression = "rate(5 minutes)"
   }
   
   resource "aws_cloudwatch_event_target" "lambda" {
     rule      = aws_cloudwatch_event_rule.lambda_warmer.name
     target_id = "lambda"
     arn       = aws_lambda_function.websocket_handler.arn
     
     input = jsonencode({
       "requestContext": {
         "routeKey": "warmer"
       }
     })
   }
   ```
   - 5分ごとに呼び出してLambda実行環境を温かく保つ
   - 月間リクエスト数: 8,640回（無料枠100万回に対して1%未満）
   - 追加コスト: ほぼゼロ

---

## 📊 各ソリューションの比較表

| ソリューション | コールドスタート削減 | 追加コスト | 実装難易度 | 推奨度 | 利用可能時期 |
|--------------|---------------------|-----------|-----------|-------|------------|
| **Lambda SnapStart** | 80-90% | $0 | ⭐ | ⭐⭐⭐⭐⭐ | Python 3.13 GA待ち |
| **ECS Fargate** | 100% | ~$35/月 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 今すぐ |
| **Lambda Warmer** | 50-70% | ~$0 | ⭐⭐ | ⭐⭐⭐⭐ | 今すぐ |
| **Lambda最適化** | 20-30% | $0-2/月 | ⭐ | ⭐⭐⭐⭐ | 今すぐ |
| **Provisioned Concurrency** | 100% | ~$12/月 | ⭐ | ❌ | 使いたくない |

---

## 🎬 アクションプラン

### フェーズ1: 今すぐ実施（無料）

```bash
# 1. Lambda関数の最適化
# - グローバルスコープでの初期化
# - メモリサイズ増加（128MB → 256MB）

# 2. Lambda Warmer実装
cd terraform
# warmer.tfを追加
terraform apply
```

**期待効果:**
- コールドスタート発生率: 50-70%削減
- 追加コスト: $0-1/月

### フェーズ2: Python 3.13 GA後（2025 Q1-Q2予定）

```bash
# 1. Python 3.13互換性テスト
# 2. SnapStart有効化

cd terraform
# main.tfを更新（snap_startブロック追加）
terraform apply
```

**期待効果:**
- コールドスタート時間: 80-90%削減（200-500ms → 50-100ms）
- 追加コスト: $0

### フェーズ3: トラフィック増加時（必要に応じて）

```bash
# ECS Fargateへの移行を検討
# - 月間100万リクエスト以上
# - WebSocket接続2時間以上必要
# - コストよりパフォーマンス優先
```

---

## 💡 結論

### 今すぐやるべきこと

✅ **Lambda Warmer + 関数最適化** を実装
   - 無料で50-70%のコールドスタート削減
   - 実装時間: 30分程度

### 近い将来（2025 Q1-Q2）

✅ **Python 3.13 + SnapStart** に移行
   - 追加コスト$0で80-90%削減
   - 実装時間: 1-2時間

### 高トラフィック時の選択肢

✅ **ECS Fargate** への移行を検討
   - 完全なコールドスタート削減
   - 月$35程度の追加コスト

**最終的な答え:**
プロビジョニング済み同時実行を使わずにコールドスタートをほぼゼロにする方法は**Lambda SnapStart（Python 3.13）**です！ただし、GAまで待つ必要があります。それまでは**Lambda Warmer**で凌ぐのがベストです。
