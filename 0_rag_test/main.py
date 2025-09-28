import json
from pprint import pprint

import boto3
#from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient
#from mypy_boto3_bedrock_agent.client import AgentsforBedrockClient
#from mypy_boto3_bedrock_agent_runtime.client import AgentsforBedrockRuntimeClient

knowledge_base_id = "4YA8ALSREY"
data_source_id = "BMXG7HDVAG"

# 推論用テキストモデルの情報
model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
region = "us-west-2"

#agents_client = boto3.client("bedrock-agent", region_name=region)
agents_runtime_client = boto3.client("bedrock-agent-runtime", region_name=region)
bedrock_runtime_client = boto3.client("bedrock-runtime", region_name=region)

# test_query = "東京都　人口"
# response = agents_runtime_client.retrieve(
#     knowledgeBaseId=knowledge_base_id,
#     retrievalConfiguration={
#         "vectorSearchConfiguration": {
#             "overrideSearchType": "SEMANTIC", # "SEMANTIC"にするとベクター検索結果だけ帰ってきます
#             "numberOfResults": 3
#         }
#     },
#     retrievalQuery={
#         "text": test_query
#     }
# )

# pprint(response)

# プロンプトテンプレート
prompt_template = \
"""下記<context></context>はユーザーから問い合わせられた質問に対して関係があると思われる検索結果の一覧です。
注意深く読んでください。
<context>
{context}
</context>
あなたは親切なAIボットです。ユーザからの質問に対して<context></context>で与えられている情報をもとに誠実に回答します。
ただし、質問に対する答えが<context></context>に書かれていない場合は、正直に「分かりません。」と回答してください。

下記<question></question>がユーザーからの質問です。
<question>
{question}
</question>
ユーザーからの質問に回答してください。

なお、ユーザーからの質問に回答する前に<thinking></thinking>タグで思考過程を記してから回答内容を<answer></answer>に加えてください。
"""

def retrieve_context(
        query: str, 
        knowledge_base_id: str, 
        agents_runtime_client
    ) -> list[dict]:
    """
    ナレッジベースに対して検索をかけて関連するドキュメントを取得する
    """
    response = agents_runtime_client.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "overrideSearchType": "SEMANTIC",  # "SEMANTIC"にするとベクター検索結果だけ帰ってきます
                "numberOfResults": 3
            }
        },
        retrievalQuery={
            "text": query
        }
    )
    print("【DEBUG】retrieve_context:")
    pprint(response)
    return response["retrievalResults"]

def invoke_llm(
        prompt: str,
        model_id: str,
        bedrock_runtime_client
) -> str:
    """
    Converse API を使って、LLMを呼び出す
    """
    response = bedrock_runtime_client.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        inferenceConfig={
            "temperature": 0.0
        }
    )
    print("【DEBUG】invoke_llm:")
    pprint(response)
    result = response['output']['message']['content'][0]['text']
    return result

def ask_question_naive_rag(
        question: str,
        knowledge_base_id: str,
        agents_runtime_client,
        bedrock_runtime_client
) -> str:
    """
    質問→検索→LLM→回答　という最もシンプルな流れを実現する関数
    """
    context = retrieve_context(question, knowledge_base_id, agents_runtime_client)
    prompt = prompt_template.format(
        context=json.dumps(context),
        question=question
    )
    print("retrieved context")
    print("="*30)
    print("\n".join(_context["content"]["text"] for _context in context))
    print("="*30)
    # LLMを呼び出す
    llm_response = invoke_llm(prompt, model_id, bedrock_runtime_client)
    return llm_response


answer = ask_question_naive_rag(
    "東京都の地下鉄路線一覧を教えて。",
    knowledge_base_id,
    agents_runtime_client,
    bedrock_runtime_client
)
print("answer:", answer)
