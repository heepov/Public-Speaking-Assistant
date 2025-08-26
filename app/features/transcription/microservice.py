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
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import aiofiles

from app.core.config import settings
from app.core.logger import setup_logger
from app.features.transcription.service import TranscriptionService

# Настройка логирования
logger = setup_logger(__name__)

# Инициализация сервиса транскрипции
transcription_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global transcription_service
    
    # Startup
    logger.info("🚀 Starting transcription microservice...")
    
    try:
        # Инициализация сервиса транскрипции
        transcription_service = TranscriptionService()
        await transcription_service.initialize()
        
        logger.info("✅ Transcription microservice successfully initialized")
        
    except Exception as e:
        logger.error(f"❌ Error initializing transcription service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down transcription microservice...")


# Создание FastAPI приложения с lifespan
app = FastAPI(
    title="Transcription Microservice",
    description="Микросервис для транскрипции аудио файлов с поддержкой GPU",
    version="1.0.0",
    lifespan=lifespan
)

# Создание директорий
settings.create_directories()

# Настройка CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов для веб-интерфейса
web_dir = Path(__file__).parent / "web"
if web_dir.exists():
    app.mount("/web", StaticFiles(directory=str(web_dir)), name="web")


@app.get("/")
async def root():
    """Корневой маршрут - перенаправление на веб-интерфейс"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Transcription Service</title>
        <meta http-equiv="refresh" content="0; url=/web/index.html">
    </head>
    <body>
        <p>Перенаправление на веб-интерфейс... <a href="/web/index.html">Нажмите здесь</a></p>
    </body>
    </html>
    """)


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        if transcription_service is None:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": "Service not initialized"}
            )
        
        # Проверяем доступность GPU
        gpu_status = "available" if transcription_service.device == "cuda" else "cpu_only"
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "transcription",
                "device": transcription_service.device,
                "gpu_status": gpu_status,
                "model_size": transcription_service.model_size,
                "language": transcription_service.language
            }
        )
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )


@app.post("/transcribe")
async def transcribe_file(
    file: UploadFile = File(...),
    task_id: str = Form(...),
    model_size: str = Form("base")
):
    """
    Эндпоинт для транскрипции аудио файла
    
    Args:
        file: Загружаемый аудио файл
        task_id: ID задачи
        model_size: Размер модели Whisper (tiny, base, small, medium, large-v2, large-v3)
        
    Returns:
        JSON с результатами транскрипции
    """
    
    logger.info(f"📤 Received audio file for transcription: {file.filename} (task_id: {task_id})")
    
    # Проверка формата файла - только аудио файлы
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.SUPPORTED_AUDIO_FORMATS:
        logger.error(f"❌ Unsupported audio format: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Supported formats: {', '.join(settings.SUPPORTED_AUDIO_FORMATS)}"
        )
    
    try:
        # Сохранение загруженного файла
        file_path = settings.UPLOAD_DIR / file.filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"💾 Audio file saved: {file_path}")
        
        # Проверяем, что это аудио файл
        if not transcription_service.is_audio_file(file_path):
            raise HTTPException(
                status_code=400,
                detail="File is not a supported audio file"
            )
        
        # Установка модели если указана
        if model_size != transcription_service.model_size:
            logger.info(f"🔄 Switching model from {transcription_service.model_size} to {model_size}")
            transcription_service.model_size = model_size
            # Переинициализируем сервис с новой моделью
            await transcription_service.initialize()
        
        # Выполняем транскрипцию
        logger.info(f"🎯 Starting transcription with model: {model_size}")
        
        result = await transcription_service.transcribe_audio_file(
            audio_path=file_path,
            task_id=task_id
        )
        
        logger.info(f"✅ Transcription completed for task: {task_id}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "filename": file.filename,
                "model_used": model_size,
                "device_used": transcription_service.device,
                "result": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Transcription error for task {task_id}: {e}")
        
        # Очистка файлов в случае ошибки
        try:
            if file_path.exists():
                file_path.unlink()
        except:
            pass
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "task_id": task_id,
                "message": f"Transcription failed: {str(e)}"
            }
        )


@app.post("/transcribe/batch")
async def transcribe_batch(
    files: list[UploadFile] = File(...),
    task_id: str = Form(...),
    model_size: str = Form("base")
):
    """
    Эндпоинт для пакетной транскрипции аудио файлов
    
    Args:
        files: Список загружаемых аудио файлов
        task_id: ID задачи
        model_size: Размер модели Whisper
        
    Returns:
        JSON с результатами транскрипции
    """
    
    logger.info(f"📤 Received batch transcription request: {len(files)} files (task_id: {task_id})")
    
    results = []
    errors = []
    
    try:
        # Установка модели если указана
        if model_size != transcription_service.model_size:
            logger.info(f"🔄 Switching model from {transcription_service.model_size} to {model_size}")
            transcription_service.model_size = model_size
            await transcription_service.initialize()
        
        for i, file in enumerate(files):
            try:
                # Проверка формата файла
                file_extension = Path(file.filename).suffix.lower()
                if file_extension not in settings.SUPPORTED_AUDIO_FORMATS:
                    errors.append({
                        "filename": file.filename,
                        "error": f"Unsupported audio format: {file_extension}"
                    })
                    continue
                
                # Сохранение файла
                file_path = settings.UPLOAD_DIR / f"{task_id}_{i}_{file.filename}"
                
                async with aiofiles.open(file_path, 'wb') as f:
                    content = await file.read()
                    await f.write(content)
                
                # Проверка аудио файла
                if not transcription_service.is_audio_file(file_path):
                    errors.append({
                        "filename": file.filename,
                        "error": "File is not a supported audio file"
                    })
                    continue
                
                # Транскрипция
                logger.info(f"🎯 Transcribing file {i+1}/{len(files)}: {file.filename}")
                
                result = await transcription_service.transcribe_audio_file(
                    audio_path=file_path,
                    task_id=f"{task_id}_{i}"
                )
                
                results.append({
                    "filename": file.filename,
                    "task_id": f"{task_id}_{i}",
                    "result": result
                })
                
                logger.info(f"✅ File {i+1}/{len(files)} transcribed successfully")
                
            except Exception as e:
                logger.error(f"❌ Error transcribing file {file.filename}: {e}")
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "completed",
                "task_id": task_id,
                "total_files": len(files),
                "successful": len(results),
                "failed": len(errors),
                "model_used": model_size,
                "device_used": transcription_service.device,
                "results": results,
                "errors": errors
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Batch transcription error for task {task_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "task_id": task_id,
                "message": f"Batch transcription failed: {str(e)}"
            }
        )


@app.get("/models")
async def get_available_models():
    """Получение информации о доступных моделях"""
    try:
        return JSONResponse(
            status_code=200,
            content={
                "current_model": transcription_service.model_size,
                "current_language": transcription_service.language,
                "available_models": ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
                "device": transcription_service.device,
                "gpu_available": transcription_service.device == "cuda"
            }
        )
    except Exception as e:
        logger.error(f"❌ Error getting models info: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/download/{filename}")
async def download_transcription(filename: str):
    """Скачивание файла транскрипции"""
    try:
        file_path = settings.OUTPUT_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File {filename} not found"
            )
        
        logger.info(f"📥 Downloading transcription file: {filename}")
        
        # Определяем MIME тип по расширению
        if filename.endswith('.txt'):
            media_type = "text/plain"
        elif filename.endswith('.json'):
            media_type = "application/json"
        elif filename.endswith('.srt'):
            media_type = "text/plain"
        else:
            media_type = "text/plain"
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading transcription file {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading file: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.features.transcription.microservice:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )
