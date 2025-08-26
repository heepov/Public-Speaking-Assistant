#!/usr/bin/env python3
"""
Тест для проверки Ollama Processing API
"""

import requests
import json
from datetime import datetime

def test_ollama_api():
    """Тестирование Ollama API"""
    
    base_url = "http://localhost:8004"
    
    print("🧪 Тестирование Ollama Processing API")
    print("=" * 50)
    
    # Тест 1: Только промпт без входных данных
    print("\n1️⃣ Тест: Только промпт")
    try:
        response = requests.post(
            f"{base_url}/process-json",
            data={
                "prompt": "Расскажи мне о преимуществах искусственного интеллекта в современном мире",
                "task_id": f"test-only-prompt-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "model_name": "llama2",
                "use_openai": "false"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успешно!")
            print(f"   Статус: {result['status']}")
            print(f"   Модель: {result['model']}")
            print(f"   Результат (начало): {result['result'][:100]}...")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 2: Промпт с входными данными
    print("\n2️⃣ Тест: Промпт с входными данными")
    try:
        test_data = {
            "title": "Тестовая презентация",
            "content": "Это тестовое содержание для проверки работы API.",
            "author": "Тестовый автор"
        }
        
        response = requests.post(
            f"{base_url}/process-json",
            data={
                "prompt": "Проанализируй эту презентацию и создай краткое резюме",
                "data": json.dumps(test_data),
                "task_id": f"test-with-data-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "model_name": "llama2",
                "use_openai": "false"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успешно!")
            print(f"   Статус: {result['status']}")
            print(f"   Модель: {result['model']}")
            print(f"   Результат (начало): {result['result'][:100]}...")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 3: Проверка health endpoint
    print("\n3️⃣ Тест: Health check")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Сервис работает!")
            print(f"   Статус: {result['status']}")
            print(f"   Сервис: {result['service']}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 4: Проверка статуса Ollama
    print("\n4️⃣ Тест: Статус Ollama")
    try:
        response = requests.get(f"{base_url}/ollama-status", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Ollama статус получен!")
            print(f"   Статус: {result['status']}")
            print(f"   Хост: {result['host']}")
            print(f"   Моделей: {result.get('model_count', 'N/A')}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_ollama_api()
