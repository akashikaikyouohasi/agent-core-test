## メモ
### デプロイコマンド
agentcore configure --entrypoint agentcore.py --name test
agentcore launch

### 作成されるリソース
- ECR repository:
    - 206863353204.dkr.ecr.us-east-1.amazonaws.com/bedrock-agentcore-test
-  IAM role
    - execution role
        - エージェントコアのruntimeで利用するもの
        - arn:aws:iam::206863353204:role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-9f86d08188
        - IAM policy
            - BedrockAgentCoreRuntimeExecutionPolicy-test
                - カスタマーインラインポリシーで、色々な権限がついている模様
                - クロスリージョン推論プロファイルで、別リージョンのモデルも呼び出すため、BedrockModelInvocationに"arn:aws:bedrock:us-west-2:206863353204:*"を追加！
    - CodeBuild execution role
        - arn:aws:iam::206863353204:role/AmazonBedrockAgentCoreSDKCodeBuild-us-east-1-9f86d08188
        - IAM policy
            - CodeBuildExecutionPolicy
- S3 bucket
    - bedrock-agentcore-codebuild-sources-206863353204-us-east-1
- Bedrock AgentCore
    - arn:aws:bedrock-agentcore:us-east-1:206863353204:runtime/test-IZBUCp5Suw
    - endpoint
        - arn:aws:bedrock-agentcore:us-east-1:206863353204:runtime/test-IZBUCp5Suw/runtime-endpoint/DEFAULT
- CloudWatch Logs ロググループ
    - runtime
        - `/aws/bedrock-agentcore/runtimes/test-IZBUCp5Suw-DEFAULT --log-stream-name-prefix "2025/09/14/[runtime-logs]"`
    - オブザーバビリティ
        - `/aws/bedrock-agentcore/runtimes/test-IZBUCp5Suw-DEFAULT --log-stream-names "otel-rt-logs"`
- CodeBuild
    - ビルドプロジェクト
        - bedrock-agentcore-test-builder
            - S3にzipをあげてデプロイしている
