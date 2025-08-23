"""
Микросервис транскрипции
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import aiofiles

from app.core.config import settings
from app.core.logger import setup_logger
from app.features.transcription.service import TranscriptionService

# Настройка логирования
logger = setup_logger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Transcription Microservice",
    description="Микросервис для транскрипции аудио/видео файлов",
    version="1.0.0"
)

# Создание директорий
settings.create_directories()

# Инициализация сервиса транскрипции
transcription_service = None


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    global transcription_service
    
    logger.info("🚀 Запуск микросервиса транскрипции...")
    
    try:
        # Инициализация сервиса транскрипции
        transcription_service = TranscriptionService()
        await transcription_service.initialize()
        
        logger.info("✅ Микросервис транскрипции успешно инициализирован")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации сервиса транскрипции: {e}")
        raise


@app.post("/transcribe")
async def transcribe_file(
    file: UploadFile = File(...),
    task_id: str = Form(...)
):
    """
    Эндпоинт для транскрипции файла
    
    Args:
        file: Загружаемый файл
        task_id: ID задачи
        
    Returns:
        JSON с результатами транскрипции
    """
    
    logger.info(f"📤 Получен файл для транскрипции: {file.filename} (task_id: {task_id})")
    
    # Проверка формата файла
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALL_SUPPORTED_FORMATS:
        logger.error(f"❌ Неподдерживаемый формат файла: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат файла. Поддерживаемые форматы: {', '.join(settings.ALL_SUPPORTED_FORMATS)}"
        )
    
    try:
        # Сохранение загруженного файла
        file_path = settings.UPLOAD_DIR / file.filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"💾 Файл сохранен: {file_path}")
        
        # Выполнение транскрипции
        results = await transcription_service.transcribe_file(
            file_path=file_path,
            file_extension=file_extension,
            task_id=task_id,
            progress_callback=None,  # В микросервисе не нужен callback
            log_callback=lambda level, msg: logger.info(f"[{level}] {msg}")
        )
        
        # Удаление временного файла
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info("🗑️ Временный файл удален")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить временный файл: {e}")
        
        return JSONResponse(results)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при транскрипции: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка транскрипции: {str(e)}")


@app.get("/health")
async def health_check():
    """Проверка состояния микросервиса"""
    return {
        "status": "healthy",
        "service": "transcription",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    # Получаем порт из переменной окружения или используем по умолчанию
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Запуск микросервиса транскрипции на {host}:{port}")
    
    uvicorn.run(
        "app.features.transcription.microservice:app",
        host=host,
        port=port,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )
