FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim
WORKDIR /app

# All environment variables in one layer
# UV_SYSTEM_PYTHONは、uvがシステムのPythonを直接使用
# UV_COMPILE_BYTECODEは、Pythonバイトコードを事前コンパイルし、初回起動こ高速化
# UV_NO_PROGRESSは、uvプログレスバーを非表示し、ログをすっきりさせる
# PYTHONUNBUFFEREDは、Pythonの標準出力と標準エラーをバッファリングせずに即座に出力
# DOCKER_CONTAINERは、カスタム環境変数で、アプリケーションがDockerコンテナ内で実行していることを示す。実行環境情報
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=us-west-2 \
    AWS_DEFAULT_REGION=us-west-2



COPY requirements.txt requirements.txt
# Install from requirements file
RUN uv pip install -r requirements.txt




RUN uv pip install aws-opentelemetry-distro>=0.10.1


# Set AWS region environment variable

ENV AWS_REGION=us-west-2
ENV AWS_DEFAULT_REGION=us-west-2


# Signal that this is running in Docker for host binding logic
# カスタム環境変数で、アプリケーションに「Docker コンテナ内で実行されている」ことを伝えるためのフラグです。
ENV DOCKER_CONTAINER=1

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

# Copy entire project (respecting .dockerignore)
COPY . .

# Use the full module path

CMD ["opentelemetry-instrument", "python", "-m", "agents"]
