#!/bin/bash

echo "🚀 Настройка Ollama для анализа текста..."

# Проверяем, что Ollama запущен
echo "Проверяем статус Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama не запущен. Запустите 'ollama serve' или используйте docker-compose.ollama.yml"
    exit 1
fi

echo "✅ Ollama запущен"

# Устанавливаем модели
echo "📥 Устанавливаем модели..."

# Llama 2 (базовая модель)
echo "Устанавливаем Llama 2..."
ollama pull llama2

# Mistral (быстрая и точная)
echo "Устанавливаем Mistral..."
ollama pull mistral

# Code Llama (для технических текстов)
echo "Устанавливаем Code Llama..."
ollama pull codellama

# Llama 3 (новая модель)
echo "Устанавливаем Llama 3..."
ollama pull llama3

# Phi-3 (легкая модель)
echo "Устанавливаем Phi-3..."
ollama pull phi3

echo "✅ Все модели установлены!"
echo ""
echo "Доступные модели:"
ollama list
echo ""
echo "🎉 Настройка завершена! Теперь вы можете использовать анализ текста в приложении."
