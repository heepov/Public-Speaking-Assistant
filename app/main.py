"""
Основной FastAPI сервер для обработки медиа файлов
"""

import os
import logging
import tempfile
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import uvicorn
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiofiles

from app.core.config import settings
from app.core.logger import setup_logger, get_recent_logs

# Настройка логирования
logger = setup_logger(__name__)

def sanitize_filename(filename: str) -> str:
    """Санитизация имени файла для безопасной обработки"""
    # Убираем или заменяем проблемные символы
    sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
    # Убираем множественные подчеркивания
    sanitized = re.sub(r'_+', '_', sanitized)
    # Убираем подчеркивания в начале и конце
    sanitized = sanitized.strip('_')
    return sanitized

# Создание FastAPI приложения
app = FastAPI(
    title=settings.APP_NAME,
    description="Мощный инструмент для обработки медиа файлов с поддержкой конвертации и транскрипции",
    version=settings.APP_VERSION
)

# Создание директорий
settings.create_directories()

# Инициализация сервисов (теперь только HTTP-клиенты для микросервисов)

# Настройки микросервисов
MICROSERVICES_CONFIG = {
    "transcription_service": {
        "url": "http://media-processor-transcription:8001",
        "health_endpoint": "/health"
    },
    "video_converter": {
        "url": "http://media-processor-converter:8002", 
        "health_endpoint": "/health"
    }
}

# Словарь для хранения статусов задач
task_statuses: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    
    logger.info("🚀 Запуск сервиса обработки медиа файлов...")
    
    try:
        # Проверка доступности микросервисов
        await check_microservices_health()
        
        logger.info("✅ Все сервисы успешно инициализированы")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации сервисов: {e}")
        raise


async def check_microservices_health():
    """Проверка доступности микросервисов"""
    logger.info("🔍 Проверяем доступность микросервисов...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, config in MICROSERVICES_CONFIG.items():
            try:
                health_url = f"{config['url']}{config['health_endpoint']}"
                response = await client.get(health_url)
                
                if response.status_code == 200:
                    logger.info(f"✅ {service_name} доступен")
                else:
                    logger.warning(f"⚠️ {service_name} отвечает с кодом {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"⚠️ {service_name} недоступен: {e}")
                # Не прерываем запуск основного приложения, если микросервисы недоступны
                # Они могут запуститься позже


async def call_transcription_service(file_path: Path, task_id: str, model_size: str = "base") -> Dict[str, Any]:
    """Вызов микросервиса транскрипции"""
    
    transcription_url = f"{MICROSERVICES_CONFIG['transcription_service']['url']}/transcribe"
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 минут таймаут
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                data = {'task_id': task_id, 'model_size': model_size}
                
                response = await client.post(transcription_url, files=files, data=data)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ошибка микросервиса транскрипции: {response.text}"
                    )
                    
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Таймаут микросервиса транскрипции")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка вызова микросервиса транскрипции: {str(e)}")


async def get_transcription_status(task_id: str) -> Dict[str, Any]:
    """Получение статуса транскрипции от микросервиса"""
    
    status_url = f"{MICROSERVICES_CONFIG['transcription_service']['url']}/status/{task_id}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(status_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ошибка получения статуса: {response.text}"
                )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")


async def call_video_converter_service(file_path: Path, task_id: str) -> Dict[str, Any]:
    """Вызов микросервиса конвертации видео в аудио"""
    
    converter_url = f"{MICROSERVICES_CONFIG['video_converter']['url']}/convert"
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 минут таймаут
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                data = {'task_id': task_id}
                
                response = await client.post(converter_url, files=files, data=data)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ошибка микросервиса конвертации: {response.text}"
                    )
                    
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Таймаут микросервиса конвертации")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка вызова микросервиса конвертации: {str(e)}")


@app.get("/models")
async def get_available_models():
    """Получение списка доступных моделей"""
    try:
        models_url = f"{MICROSERVICES_CONFIG['transcription_service']['url']}/models"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(models_url)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail="Ошибка получения моделей")
    except Exception as e:
        logger.error(f"❌ Ошибка получения моделей: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения моделей: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def get_main_page():
    """Главная страница с выбором фич"""
    
    # Читаем HTML шаблон
    template_path = Path(__file__).parent / "web" / "templates" / "index.html"
    
    try:
        async with aiofiles.open(template_path, 'r', encoding='utf-8') as f:
            html_content = await f.read()
        
        # Заменяем переменные в шаблоне
        html_content = html_content.replace("{{ app_name }}", settings.APP_NAME)
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки шаблона: {e}")
        return HTMLResponse(content="<h1>Ошибка загрузки интерфейса</h1>")


@app.post("/process")
async def process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    feature: str = Form(...),
    model_size: str = Form("base")
):
    """
    Эндпоинт для обработки файла с выбором фичи
    
    Args:
        file: Загружаемый файл
        feature: Выбранная фича ('video-to-audio' или 'transcription')
        
    Returns:
        JSON с task_id для отслеживания прогресса
    """
    
    logger.info(f"📤 Получен файл для обработки: {file.filename} (фича: {feature})")
    
    # Санитизация имени файла
    original_filename = file.filename
    safe_filename = sanitize_filename(file.filename)
    
    # Проверка формата файла
    file_extension = Path(original_filename).suffix.lower()
    if file_extension not in settings.ALL_SUPPORTED_FORMATS:
        logger.error(f"❌ Неподдерживаемый формат файла: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат файла. Поддерживаемые форматы: {', '.join(settings.ALL_SUPPORTED_FORMATS)}"
        )
    
    # Проверка выбранной фичи
    if feature not in ['video-to-audio', 'transcription']:
        raise HTTPException(
            status_code=400,
            detail="Неверная фича. Доступные фичи: 'video-to-audio', 'transcription'"
        )
    
    # Создание уникального ID задачи
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_filename}"
    logger.info(f"🆔 Создана задача с ID: {task_id}")
    
    try:
        # Сохранение загруженного файла с безопасным именем
        file_path = settings.UPLOAD_DIR / safe_filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"💾 Файл сохранен: {file_path}")
        
        # Добавление задачи в фоновую обработку
        if feature == 'transcription':
            background_tasks.add_task(
                process_transcription_task,
                task_id,
                file_path,
                file_extension,
                model_size
            )
        elif feature == 'video-to-audio':
            background_tasks.add_task(
                process_video_to_audio_task,
                task_id,
                file_path,
                file_extension
            )
        
        return JSONResponse({
            "task_id": task_id,
            "message": "Файл загружен, начинается обработка",
            "filename": original_filename,
            "safe_filename": safe_filename,
            "feature": feature
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке файла: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке файла: {str(e)}")


async def process_transcription_task(task_id: str, file_path: Path, file_extension: str, model_size: str = "base"):
    """Фоновая обработка задачи транскрипции"""
    
    # Инициализация статуса задачи
    task_statuses[task_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Начинаем транскрипцию...",
        "logs": [],
        "error": None,
        "result_file": None
    }
    
    def add_log(level: str, message: str):
        """Добавление лога в статус задачи"""
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message
        }
        task_statuses[task_id]["logs"].append(log_entry)
        logger.info(f"[{task_id}] {level}: {message}")
    
    try:
        add_log("INFO", f"🚀 Отправляем файл в микросервис транскрипции: {file_path.name}")
        
        # Обновление прогресса
        task_statuses[task_id].update({
            "progress": 10,
            "message": "Отправляем файл в микросервис транскрипции..."
        })
        
                # Вызов микросервиса транскрипции
        results = await call_transcription_service(file_path, task_id, model_size)
        
        add_log("INFO", "✅ Получен ответ от микросервиса транскрипции")
        
        # Сохранение результатов в два файла
        simple_output_file = settings.OUTPUT_DIR / f"{task_id}_simple.txt"
        detailed_output_file = settings.OUTPUT_DIR / f"{task_id}_detailed.txt"
        
        async with aiofiles.open(simple_output_file, 'w', encoding='utf-8') as f:
            await f.write(results['simple_text'])
        
        async with aiofiles.open(detailed_output_file, 'w', encoding='utf-8') as f:
            await f.write(results['detailed_text'])
        
        add_log("SUCCESS", f"✅ Транскрипция завершена успешно")
        
        # Обновление финального статуса
        task_statuses[task_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Транскрипция завершена!",
            "simple_file": str(simple_output_file),
            "detailed_file": str(detailed_output_file)
        })
        
    except Exception as e:
        add_log("ERROR", f"❌ Ошибка при транскрипции: {str(e)}")
        
        task_statuses[task_id].update({
            "status": "failed",
            "progress": 0,
            "message": "Ошибка при обработке",
            "error": str(e)
        })
        
    finally:
        # Удаление временного файла
        try:
            if file_path.exists():
                file_path.unlink()
                add_log("INFO", "🗑️ Временный файл удален")
        except Exception as e:
            add_log("WARNING", f"⚠️ Не удалось удалить временный файл: {e}")


async def process_video_to_audio_task(task_id: str, file_path: Path, file_extension: str):
    """Фоновая обработка задачи конвертации видео в аудио"""
    
    # Инициализация статуса задачи
    task_statuses[task_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Начинаем конвертацию...",
        "logs": [],
        "error": None,
        "result_file": None
    }
    
    def add_log(level: str, message: str):
        """Добавление лога в статус задачи"""
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message
        }
        task_statuses[task_id]["logs"].append(log_entry)
        logger.info(f"[{task_id}] {level}: {message}")
    
    try:
        add_log("INFO", f"🚀 Отправляем файл в микросервис конвертации: {file_path.name}")
        
        # Обновление прогресса
        task_statuses[task_id].update({
            "progress": 10,
            "message": "Отправляем файл в микросервис конвертации..."
        })
        
        # Вызов микросервиса конвертации
        results = await call_video_converter_service(file_path, task_id)
        
        add_log("INFO", "✅ Получен ответ от микросервиса конвертации")
        
        add_log("SUCCESS", f"✅ Конвертация завершена успешно")
        
        # Обновление финального статуса
        task_statuses[task_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Конвертация завершена!",
            "audio_file": results.get("audio_file")
        })
        
    except Exception as e:
        add_log("ERROR", f"❌ Ошибка при конвертации: {str(e)}")
        
        task_statuses[task_id].update({
            "status": "failed",
            "progress": 0,
            "message": "Ошибка при обработке",
            "error": str(e)
        })
        
    finally:
        # Удаление временного файла
        try:
            if file_path.exists():
                file_path.unlink()
                add_log("INFO", "🗑️ Временный файл удален")
        except Exception as e:
            add_log("WARNING", f"⚠️ Не удалось удалить временный файл: {e}")


@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Получение статуса задачи
    
    Args:
        task_id: ID задачи
        
    Returns:
        JSON со статусом задачи
    """
    
    if task_id not in task_statuses:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return JSONResponse(task_statuses[task_id])


@app.get("/download/{task_id}/{file_type}")
async def download_result(task_id: str, file_type: str):
    """
    Скачивание результата обработки
    
    Args:
        task_id: ID задачи
        file_type: Тип файла ('simple', 'detailed', или 'audio')
        
    Returns:
        Файл с результатом обработки
    """
    
    if task_id not in task_statuses:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    task_status = task_statuses[task_id]
    
    if task_status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Задача еще не завершена")
    
    if file_type == "simple":
        result_file = task_status.get("simple_file")
        filename = f"{task_id}_simple.txt"
    elif file_type == "detailed":
        result_file = task_status.get("detailed_file")
        filename = f"{task_id}_detailed.txt"
    elif file_type == "audio":
        result_file = task_status.get("audio_file")
        filename = f"{task_id}_audio.wav"
    else:
        raise HTTPException(status_code=400, detail="Неверный тип файла. Используйте 'simple', 'detailed' или 'audio'")
    
    if not result_file or not Path(result_file).exists():
        raise HTTPException(status_code=404, detail="Файл результата не найден")
    
    return FileResponse(
        path=result_file,
        filename=filename,
        media_type="text/plain" if file_type in ["simple", "detailed"] else "audio/wav"
    )


@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    
    # Проверяем доступность микросервисов
    microservices_status = {}
    
    for service_name, config in MICROSERVICES_CONFIG.items():
        try:
            health_url = f"{config['url']}{config['health_endpoint']}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(health_url)
                if response.status_code == 200:
                    logger.info(f"✅ Микросервис {service_name} доступен")
                    microservices_status[service_name] = "healthy"
                else:
                    logger.warning(f"⚠️ Микросервис {service_name} отвечает с кодом {response.status_code}")
                    microservices_status[service_name] = "unhealthy"
        except Exception as e:
            logger.warning(f"⚠️ Микросервис {service_name} недоступен: {e}")
            microservices_status[service_name] = "unavailable"

    # Определяем общий статус
    all_healthy = all(status == "healthy" for status in microservices_status.values())
    overall_status = "healthy" if all_healthy else "degraded"

    return JSONResponse({
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "supported_formats": list(settings.ALL_SUPPORTED_FORMATS),
        "features": ["video-to-audio", "transcription"],
        "architecture": "microservices",
        "microservices": microservices_status
    })


@app.get("/logs")
async def get_logs(limit: int = 100):
    """Получение последних логов"""
    
    logs = get_recent_logs(limit)
    return JSONResponse({"logs": logs})


if __name__ == "__main__":
    logger.info("🎬 Запуск сервиса обработки медиа файлов...")
    
    # Получаем настройки из переменных окружения
    host = settings.HOST
    port = settings.PORT
    log_level = settings.LOG_LEVEL.lower()  # uvicorn требует строчные буквы
    
    # В Docker используем 0.0.0.0 для доступа извне
    if settings.DOCKER_ENV:
        host = "0.0.0.0"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,  # Отключаем reload в Docker
        log_level=log_level
    )
