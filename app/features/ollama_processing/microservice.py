"""
Микросервис для обработки текста с помощью Ollama
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import JSONResponse
import aiofiles

from app.core.config import settings
from app.core.logger import setup_logger
from app.features.ollama_processing.service import OllamaProcessingService

# Настройка логирования
logger = setup_logger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Ollama Processing Microservice",
    description="Микросервис для обработки текста с помощью Ollama",
    version="1.0.0"
)

# Создание директорий
settings.create_directories()

# Инициализация сервиса Ollama
ollama_service = None


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    global ollama_service
    
    logger.info("🚀 Запуск микросервиса Ollama обработки...")
    
    try:
        # Инициализация сервиса Ollama
        ollama_service = OllamaProcessingService()
        await ollama_service.initialize()
        
        logger.info("✅ Микросервис Ollama обработки успешно инициализирован")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации сервиса Ollama: {e}")
        raise


@app.post("/process")
async def process_text(
    prompt: str = Form(...),
    input_file: Optional[UploadFile] = File(None),
    task_id: str = Form(...),
    instructions_file: Optional[UploadFile] = File(None),
    model_name: str = Form("llama2"),
    use_openai: bool = Form(False),
    system_prompt: Optional[str] = Form(None),
    model_params: Optional[str] = Form(None)
):
    """
    Обработка текста с помощью Ollama или OpenAI
    Автоматически загружает модель если она не установлена
    """
    try:
        logger.info(f"🔄 Получен запрос на обработку - task_id: {task_id}")
        logger.info(f"🤖 Запрошенная модель: {model_name}")
        
        # Инициализируем сервис если нужно
        if not ollama_service.is_initialized:
            await ollama_service.initialize()
        
        # Проверяем и загружаем модель если нужно
        if not use_openai:
            await ensure_model_available(model_name)
        
        # Подготавливаем входные данные
        input_data = None
        if input_file:
            content = await input_file.read()
            try:
                input_data = json.loads(content.decode('utf-8'))
            except json.JSONDecodeError:
                input_data = content.decode('utf-8')
        
        # Подготавливаем инструкции
        instructions_content = None
        if instructions_file:
            instructions_path = f"/tmp/instructions_{task_id}.md"
            with open(instructions_path, 'wb') as f:
                f.write(await instructions_file.read())
        else:
            instructions_path = None
        
        # Парсим параметры модели
        parsed_model_params = None
        if model_params:
            try:
                parsed_model_params = json.loads(model_params)
                logger.info(f"🔧 Получены параметры модели: {parsed_model_params}")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Не удалось распарсить параметры модели: {e}")
        
        # Обрабатываем текст
        result = await ollama_service.process_text(
            prompt=prompt,
            input_data=input_data,
            instructions_file=instructions_path,
            task_id=task_id,
            model_name=model_name,
            use_openai=use_openai,
            system_prompt=system_prompt,
            model_params=parsed_model_params
        )
        
        # Очищаем временные файлы
        if instructions_path and os.path.exists(instructions_path):
            os.remove(instructions_path)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке: {e}")
        return {
            "error": str(e),
            "task_id": task_id,
            "status": "error"
        }

async def ensure_model_available(model_name: str):
    """Проверяет доступность модели и загружает её при необходимости"""
    try:
        logger.info(f"🔍 Проверяем доступность модели: {model_name}")
        
        # Получаем список доступных моделей
        available_models = await ollama_service.list_models()
        logger.info(f"📦 Доступные модели: {available_models}")
        
        if model_name not in available_models:
            logger.info(f"📥 Модель {model_name} не найдена, начинаем загрузку...")
            
            # Загружаем модель
            success = await ollama_service.install_model(model_name)
            if not success:
                raise Exception(f"Не удалось загрузить модель {model_name}")
            
            logger.info(f"✅ Модель {model_name} успешно загружена")
        else:
            logger.info(f"✅ Модель {model_name} уже доступна")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке/загрузке модели: {e}")
        raise

@app.post("/process-json")
async def process_json_data(
    prompt: str = Form(...),
    data: Optional[Dict[str, Any]] = None,
    task_id: str = Form(...),
    instructions_file: Optional[UploadFile] = File(None),
    model_name: str = Form("llama2"),
    use_openai: bool = Form(False),
    system_prompt: Optional[str] = Form(None),
    model_params: Optional[str] = Form(None)
):
    """
    Эндпоинт для обработки JSON данных напрямую
    
    Args:
        prompt: Промпт для обработки (обязательный)
        data: JSON данные для обработки (опционально)
        task_id: ID задачи
        instructions_file: Файл с инструкциями (опционально)
        model_name: Название модели Ollama
        use_openai: Использовать OpenAI вместо Ollama
        
    Returns:
        JSON с результатами обработки
    """
    
    logger.info(f"📤 Получен запрос на обработку JSON (task_id: {task_id})")
    
    try:
        # Сохранение файла с инструкциями если предоставлен
        instructions_path = None
        if instructions_file:
            instructions_filename = f"instructions_{task_id}_{instructions_file.filename}"
            instructions_path = settings.UPLOAD_DIR / instructions_filename
            
            async with aiofiles.open(instructions_path, 'wb') as f:
                content = await instructions_file.read()
                await f.write(content)
            
            logger.info(f"📖 Файл с инструкциями сохранен: {instructions_path}")
        
        # Парсим параметры модели
        parsed_model_params = None
        if model_params:
            try:
                parsed_model_params = json.loads(model_params)
                logger.info(f"🔧 Получены параметры модели: {parsed_model_params}")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Не удалось распарсить параметры модели: {e}")
        
        # Выполнение обработки
        results = await ollama_service.process_text(
            prompt=prompt,
            input_data=data,
            instructions_file=str(instructions_path) if instructions_path else None,
            task_id=task_id,
            model_name=model_name,
            use_openai=use_openai,
            system_prompt=system_prompt,
            model_params=parsed_model_params
        )
        
        logger.info(f"✅ Обработка JSON завершена для task_id: {task_id}")
        
        return JSONResponse(results)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


@app.post("/install-model")
async def install_model(model_name: str = Form(...)):
    """
    Эндпоинт для установки модели Ollama
    
    Args:
        model_name: Название модели для установки
        
    Returns:
        JSON с результатом установки
    """
    
    logger.info(f"📥 Запрос на установку модели: {model_name}")
    
    try:
        if not ollama_service:
            raise HTTPException(status_code=503, detail="Сервис не инициализирован")
        
        success = await ollama_service.install_model(model_name)
        
        if success:
            logger.info(f"✅ Модель {model_name} успешно установлена")
            return JSONResponse({
                "status": "success",
                "message": f"Модель {model_name} успешно установлена",
                "model_name": model_name
            })
        else:
            logger.error(f"❌ Ошибка установки модели {model_name}")
            raise HTTPException(status_code=500, detail=f"Ошибка установки модели {model_name}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при установке модели: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка установки модели: {str(e)}")


async def _load_input_data(file_path: Path) -> Any:
    """Загрузка входных данных из файла"""
    file_extension = file_path.suffix.lower()
    
    if file_extension == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif file_extension in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        # Для других форматов читаем как текст
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


@app.get("/health")
async def health_check():
    """Проверка состояния микросервиса"""
    return {
        "status": "healthy",
        "service": "ollama_processing",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/model-info")
async def get_model_info():
    """Получение информации о модели"""
    if ollama_service:
        return ollama_service.get_model_info()
    else:
        raise HTTPException(status_code=503, detail="Сервис не инициализирован")


@app.get("/models")
async def list_models():
    """Получение списка доступных моделей"""
    try:
        if not ollama_service.is_initialized:
            await ollama_service.initialize()
        
        models = await ollama_service.list_models()
        return {
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка моделей: {e}")
        return {"error": str(e)}

@app.post("/models/install")
async def install_model(model_name: str = Form(...)):
    """Установка новой модели"""
    try:
        if not ollama_service.is_initialized:
            await ollama_service.initialize()
        
        logger.info(f"📥 Запрос на установку модели: {model_name}")
        
        success = await ollama_service.install_model(model_name)
        if success:
            return {
                "status": "success",
                "message": f"Модель {model_name} успешно установлена",
                "model": model_name
            }
        else:
            return {
                "status": "error",
                "message": f"Не удалось установить модель {model_name}",
                "model": model_name
            }
    except Exception as e:
        logger.error(f"❌ Ошибка при установке модели: {e}")
        return {"error": str(e)}

@app.delete("/models/{model_name}")
async def remove_model(model_name: str):
    """Удаление модели"""
    try:
        if not ollama_service.is_initialized:
            await ollama_service.initialize()
        
        logger.info(f"🗑️ Запрос на удаление модели: {model_name}")
        
        # Используем subprocess для удаления модели
        import subprocess
        import asyncio
        
        process = await asyncio.create_subprocess_exec(
            "ollama", "rm", model_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return {
                "status": "success",
                "message": f"Модель {model_name} успешно удалена",
                "model": model_name
            }
        else:
            return {
                "status": "error",
                "message": f"Не удалось удалить модель {model_name}: {stderr.decode()}",
                "model": model_name
            }
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении модели: {e}")
        return {"error": str(e)}

@app.get("/models/info")
async def get_model_info():
    """Получение информации о моделях и системе"""
    try:
        if not ollama_service.is_initialized:
            await ollama_service.initialize()
        
        info = ollama_service.get_model_info()
        models = await ollama_service.list_models()
        
        return {
            **info,
            "available_models": models,
            "models_count": len(models)
        }
    except Exception as e:
        logger.error(f"❌ Ошибка при получении информации о моделях: {e}")
        return {"error": str(e)}


@app.get("/supported-formats")
async def get_supported_formats():
    """Получение списка поддерживаемых форматов"""
    formats = [
        {"extension": ".json", "description": "JSON данные"},
        {"extension": ".txt", "description": "Текстовый файл"},
        {"extension": ".md", "description": "Markdown файл"},
        {"extension": ".csv", "description": "CSV файл"},
        {"extension": ".xml", "description": "XML файл"}
    ]
    return {"supported_formats": formats}


@app.get("/ollama-status")
async def get_ollama_status():
    """Проверка статуса Ollama"""
    try:
        import requests
        ollama_host = os.environ.get("OLLAMA_HOST", "localhost:11434")
        response = requests.get(f"http://{ollama_host}/api/tags", timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            models = [model['name'] for model in models_data.get('models', [])]
            return {
                "status": "running",
                "host": ollama_host,
                "available_models": models,
                "model_count": len(models)
            }
        else:
            return {
                "status": "error",
                "host": ollama_host,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "status": "error",
            "host": os.environ.get("OLLAMA_HOST", "localhost:11434"),
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    
    # Получаем порт из переменной окружения или используем по умолчанию
    port = int(os.getenv("PORT", 8004))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Запуск микросервиса Ollama обработки на {host}:{port}")
    
    uvicorn.run(
        "app.features.ollama_processing.microservice:app",
        host=host,
        port=port,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )
