FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libpq-dev \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install ESLint globally for JS/TS analysis
RUN npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create workspace directory
RUN mkdir -p /workspace/repos

EXPOSE 8000
