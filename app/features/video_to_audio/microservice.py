"""
Микросервис конвертации видео в аудио
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
from app.features.video_to_audio.converter import VideoToAudioConverter

# Настройка логирования
logger = setup_logger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Video Converter Microservice",
    description="Микросервис для конвертации видео в аудио",
    version="1.0.0"
)

# Создание директорий
settings.create_directories()

# Инициализация конвертера
video_converter = None


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    global video_converter
    
    logger.info("🚀 Запуск микросервиса конвертации видео...")
    
    try:
        # Инициализация конвертера
        video_converter = VideoToAudioConverter()
        
        logger.info("✅ Микросервис конвертации видео успешно инициализирован")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации конвертера: {e}")
        raise


@app.post("/convert")
async def convert_video_to_audio(
    file: UploadFile = File(...),
    task_id: str = Form(...)
):
    """
    Эндпоинт для конвертации видео в аудио
    
    Args:
        file: Загружаемый файл
        task_id: ID задачи
        
    Returns:
        JSON с результатами конвертации
    """
    
    logger.info(f"📤 Получен файл для конвертации: {file.filename} (task_id: {task_id})")
    
    # Проверка формата файла
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.VIDEO_FORMATS:
        logger.error(f"❌ Неподдерживаемый формат видео файла: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат видео файла. Поддерживаемые форматы: {', '.join(settings.VIDEO_FORMATS)}"
        )
    
    try:
        # Сохранение загруженного файла
        file_path = settings.UPLOAD_DIR / file.filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"💾 Файл сохранен: {file_path}")
        
        # Проверяем, что это видео файл
        if not video_converter.is_video_file(file_path):
            raise RuntimeError("Файл не является видео файлом")
        
        # Конвертация в аудио
        output_path = settings.OUTPUT_DIR / f"{task_id}_audio.wav"
        
        audio_file = video_converter.convert_to_audio(
            file_path,
            output_path=output_path,
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
        
        return JSONResponse({
            "status": "completed",
            "message": "Конвертация завершена успешно",
            "audio_file": str(audio_file),
            "task_id": task_id
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка конвертации: {str(e)}")


@app.get("/health")
async def health_check():
    """Проверка состояния микросервиса"""
    return {
        "status": "healthy",
        "service": "video_converter",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    # Получаем порт из переменной окружения или используем по умолчанию
    port = int(os.getenv("PORT", 8002))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Запуск микросервиса конвертации на {host}:{port}")
    
    uvicorn.run(
        "app.features.video_to_audio.microservice:app",
        host=host,
        port=port,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )
