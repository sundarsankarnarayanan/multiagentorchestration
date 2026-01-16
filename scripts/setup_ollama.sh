#!/bin/bash

# Setup script for Ollama and RAG dependencies

echo "🤖 AI Agent System - RAG Setup"
echo "================================="

# 1. Install Ollama
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is already installed"
else
    echo "📥 Installing Ollama..."
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo "❌ Unsupported OS for automatic install. Please install Ollama manually: https://ollama.ai"
        exit 1
    fi
fi

# 2. Start Ollama Service (if not running)
if pgrep -x "ollama" > /dev/null; then
    echo "✅ Ollama service is running"
else
    echo "🚀 Starting Ollama service..."
    ollama serve &
    sleep 5  # Wait for it to start
fi

# 3. Pull Models
echo "📥 Pulling Llama2 model (this may take a while)..."
ollama pull llama2

echo "✅ Setup complete! You can now use the RAG chat features."
