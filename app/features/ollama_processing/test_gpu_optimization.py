#!/usr/bin/env python3
"""
Тестовый скрипт для проверки GPU оптимизации в Ollama
"""

import asyncio
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from service import OllamaProcessingService

async def test_gpu_optimization():
    """Тест GPU оптимизации"""
    print("🚀 Тестирование GPU оптимизации...")
    
    service = OllamaProcessingService()
    await service.initialize()
    
    # Тест 1: Проверка информации о GPU
    print("\n" + "="*60)
    print("🔍 ИНФОРМАЦИЯ О GPU")
    print("="*60)
    
    import torch
    if torch.cuda.is_available():
        print(f"✅ GPU доступен: {torch.cuda.get_device_name(0)}")
        print(f"📊 Память GPU: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        print(f"🔧 CUDA версия: {torch.version.cuda}")
    else:
        print("❌ GPU недоступен")
    
    # Тест 2: Проверка оптимизации параметров
    print("\n" + "="*60)
    print("🔧 ТЕСТ ОПТИМИЗАЦИИ ПАРАМЕТРОВ")
    print("="*60)
    
    # Тестируем с разными параметрами
    test_params = [
        None,  # Без параметров
        {"temperature": 0.7},  # Только температура
        {"num_gpu_layers": 50},  # Только GPU слои
        {"num_gpu_layers": 30, "num_ctx": 2048, "temperature": 0.8}  # Комбинированные
    ]
    
    for i, params in enumerate(test_params, 1):
        print(f"\n📋 Тест {i}: {params}")
        optimized = service._optimize_gpu_params(params)
        print(f"🔧 Оптимизировано: {optimized}")
    
    # Тест 3: Проверка доступных моделей
    print("\n" + "="*60)
    print("📦 ДОСТУПНЫЕ МОДЕЛИ")
    print("="*60)
    
    models = await service.list_models()
    if models:
        print(f"✅ Найдено моделей: {len(models)}")
        for model in models:
            print(f"  - {model}")
    else:
        print("❌ Модели не найдены")
    
    # Тест 4: Простой запрос (если есть модели)
    if models:
        print("\n" + "="*60)
        print("🧪 ТЕСТОВЫЙ ЗАПРОС")
        print("="*60)
        
        try:
            result = await service.process_text(
                prompt="Напиши короткое стихотворение про программирование",
                model_name=models[0],
                model_params={"num_gpu_layers": 32, "num_predict": 200}
            )
            print(f"✅ Результат получен: {len(result['result'])} символов")
            print(f"📄 Начало ответа: {result['result'][:100]}...")
        except Exception as e:
            print(f"❌ Ошибка при тестовом запросе: {e}")
    
    print("\n" + "="*60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_gpu_optimization())
