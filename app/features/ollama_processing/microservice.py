"""
Микросервис для обработки текста с помощью Ollama
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import torch

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import aiofiles

from app.core.config import settings
from app.core.logger import setup_logger
from app.features.ollama_processing.service import OllamaProcessingService

# Настройка логирования
logger = setup_logger(__name__)

# Pydantic модели для запросов
class ModelPullRequest(BaseModel):
    model_name: str

class ProcessRequest(BaseModel):
    text: str
    model: str = "llama2"
    task_id: str
    parameters: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    input_file_content: Optional[str] = None
    instructions_file_content: Optional[str] = None

# Создание FastAPI приложения
app = FastAPI(
    title="Ollama Processing Microservice",
    description="Микросервис для обработки текста с помощью Ollama",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создание директорий
settings.create_directories()

# Подключение статических файлов для веб-интерфейса
try:
    app.mount("/static", StaticFiles(directory="app/features/ollama_processing/web"), name="static")
except:
    pass  # Игнорируем ошибку если директория не существует

# Инициализация сервиса Ollama
ollama_service = None


async def ensure_model_available(model_name: str):
    """Проверка и установка модели если она недоступна"""
    try:
        if not ollama_service.is_initialized:
            await ollama_service.initialize()
        
        available_models = await ollama_service.list_models()
        
        if model_name not in available_models:
            logger.info(f"📥 Модель {model_name} не найдена, устанавливаем...")
            success = await ollama_service.install_model(model_name)
            if not success:
                raise Exception(f"Не удалось установить модель {model_name}")
            logger.info(f"✅ Модель {model_name} успешно установлена")
        else:
            logger.info(f"✅ Модель {model_name} уже доступна")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке/установке модели: {e}")
        raise


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
    request: ProcessRequest
):
    """
    Обработка текста с помощью Ollama (JSON endpoint)
    """
    try:
        logger.info(f"🔄 Получен JSON запрос на обработку - task_id: {request.task_id}")
        logger.info(f"🤖 Запрошенная модель: {request.model}")
        logger.info(f"📝 Полученный текст: '{request.text}'")
        logger.info(f"📝 Длина текста: {len(request.text) if request.text else 0}")
        
        start_time = datetime.now()
        
        # Инициализируем сервис если нужно
        if not ollama_service.is_initialized:
            await ollama_service.initialize()
        
        # Проверяем и загружаем модель если нужно
        await ensure_model_available(request.model)
        
        # Подготавливаем параметры
        parameters = request.parameters or {}
        
        # Нормализуем параметры (num_predict -> max_tokens)
        if 'num_predict' in parameters and 'max_tokens' not in parameters:
            parameters['max_tokens'] = parameters.pop('num_predict')
        
        # Подготавливаем входные данные
        input_data = None
        if request.input_file_content:
            try:
                input_data = json.loads(request.input_file_content)
            except json.JSONDecodeError:
                input_data = request.input_file_content
        
        # Подготавливаем инструкции
        instructions = request.instructions_file_content
        logger.info(f"📖 Инструкции из запроса: {instructions[:100] if instructions else 'Нет инструкций'}...")
        logger.info(f"📖 Тип инструкций: {type(instructions)}")
        logger.info(f"📖 Размер инструкций: {len(instructions) if instructions else 0} символов")
        if instructions:
            logger.info(f"📖 Первые 200 символов инструкций: '{instructions[:200]}...'")
            logger.info(f"📖 Инструкции будут добавлены к системному промпту: '{request.system_prompt}'")
        else:
            logger.info(f"📖 Инструкции не предоставлены")
        
        # Обрабатываем текст
        logger.info(f"📖 system_prompt из запроса: '{request.system_prompt}'")
        result = await ollama_service.process_text_full(
            prompt=request.text,
            input_data=input_data,
            instructions_file=None,
            task_id=request.task_id,
            model_name=request.model,
            use_openai=False,
            system_prompt=request.system_prompt,
            model_params=parameters,
            instructions_content=request.instructions_file_content
        )
        
        # Сохраняем результат (если не был сохранен в process_text_full)
        if isinstance(result, dict) and "output_file" in result:
            output_file = Path(result["output_file"])
        else:
            output_file = ollama_service._save_result(result, request.task_id)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            "status": "success",
            "task_id": request.task_id,
            "result": {
                "processed_text": result.get("result", result),
                "saved_files": {
                    "txt": result.get("output_file", str(output_file))
                }
            },
            "model_used": request.model,
            "device_used": "cuda" if torch.cuda.is_available() else "cpu",
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке текста: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/process/form")
async def process_text_form(
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
        instructions_path = None
        if instructions_file:
            content = await instructions_file.read()
            instructions_content = content.decode('utf-8')
            logger.info(f"📖 Инструкции из файла: {instructions_content[:100] if instructions_content else 'Нет инструкций'}...")
        else:
            logger.info("📖 Файл с инструкциями не предоставлен")
        
        # Парсим параметры модели
        parsed_model_params = None
        if model_params:
            try:
                parsed_model_params = json.loads(model_params)
                logger.info(f"🔧 Получены параметры модели: {parsed_model_params}")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Не удалось распарсить параметры модели: {e}")
        
        # Обрабатываем текст
        result = await ollama_service.process_text_full(
            prompt=prompt,
            input_data=input_data,
            instructions_file=instructions_path,
            task_id=task_id,
            model_name=model_name,
            use_openai=use_openai,
            system_prompt=system_prompt,
            model_params=parsed_model_params,
            instructions_content=instructions_content
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке: {e}")
        return {
            "error": str(e),
            "task_id": task_id,
            "status": "error"
        }



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
    try:
        # Проверяем статус Ollama
        ollama_status = "unknown"
        gpu_status = "unknown"
        device = "cpu"
        
        if torch.cuda.is_available():
            device = "cuda"
            gpu_status = "available"
        else:
            gpu_status = "not_available"
        
        # Проверяем доступность Ollama
        try:
            import requests
            ollama_host = os.environ.get("OLLAMA_HOST", "localhost:11434")
            response = requests.get(f"http://{ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                ollama_status = "running"
            else:
                ollama_status = "error"
        except:
            ollama_status = "not_available"
        
        return {
            "status": "healthy",
            "service": "ollama_processing",
            "device": device,
            "gpu_status": gpu_status,
            "ollama_status": ollama_status,
            "ollama_host": os.environ.get("OLLAMA_HOST", "localhost:11434"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "ollama_processing",
            "error": str(e),
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
        
        # Формируем список моделей с дополнительной информацией
        models_info = []
        for model_name in models:
            models_info.append({
                "name": model_name,
                "size": "Unknown",  # Ollama API не предоставляет размер напрямую
                "modified_at": datetime.now().isoformat()
            })
        
        return {
            "available_models": models_info,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "gpu_available": torch.cuda.is_available()
        }
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка моделей: {e}")
        return {"error": str(e)}

@app.post("/models/pull")
async def pull_model(request: ModelPullRequest):
    """Установка новой модели"""
    try:
        if not ollama_service.is_initialized:
            await ollama_service.initialize()
        
        logger.info(f"📥 Запрос на установку модели: {request.model_name}")
        
        success = await ollama_service.install_model(request.model_name)
        if success:
            return {
                "status": "success",
                "message": f"Модель {request.model_name} успешно установлена",
                "model": request.model_name
            }
        else:
            return {
                "status": "error",
                "message": f"Не удалось установить модель {request.model_name}",
                "model": request.model_name
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


@app.get("/")
async def root():
    """Корневой эндпоинт - возвращает веб-интерфейс"""
    try:
        return FileResponse("app/features/ollama_processing/web/index.html")
    except:
        return {"message": "Ollama Processing Service", "docs": "/docs"}

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
