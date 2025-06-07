FROM python:3.9-bullseye

# Set environment variables
ENV MLFLOW_HOME=/mlflow

# Create working directory
WORKDIR ${MLFLOW_HOME}

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gettext \
    gcc \
    build-essential \
    default-libmysqlclient-dev \
    libssl-dev \
    libffi-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install MLflow with GenAI extras
RUN pip install --upgrade pip && \
    pip install mlflow[genai] mlflow[auth] mlflow[extra] pymysql cryptography

# Default command
CMD ["mlflow", "server", "--host", "0.0.0.0"]
