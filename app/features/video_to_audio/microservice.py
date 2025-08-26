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
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import aiofiles

from app.core.config import settings
from app.core.logger import setup_logger
from app.features.video_to_audio.service import VideoToAudioService

# Настройка логирования
logger = setup_logger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Video Converter Microservice",
    description="Микросервис для конвертации видео в аудио с использованием FFmpeg",
    version="1.0.0"
)

# Инициализация сервиса
video_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global video_service
    
    # Startup
    logger.info("🚀 Starting video conversion microservice...")
    
    try:
        # Инициализация сервиса
        video_service = VideoToAudioService()
        await video_service.initialize()
        
        logger.info("✅ Video conversion microservice initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error initializing service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down video conversion microservice...")


# Создание FastAPI приложения с lifespan
app = FastAPI(
    title="Video Converter Microservice",
    description="Микросервис для конвертации видео в аудио с использованием FFmpeg",
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
        <title>Video to Audio Converter</title>
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
        if video_service is None:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": "Service not initialized"}
            )
        
        # Проверяем доступность FFmpeg
        ffmpeg_status = "available" if video_service.ffmpeg_path else "not_found"
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "video_converter",
                "ffmpeg_status": ffmpeg_status,
                "ffmpeg_path": video_service.ffmpeg_path,
                "supported_video_formats": list(video_service.VIDEO_FORMATS),
                "optimal_audio_settings": video_service.OPTIMAL_AUDIO_SETTINGS
            }
        )
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )


@app.post("/convert")
async def convert_video_to_audio(
    file: UploadFile = File(...),
    task_id: str = Form(...),
    audio_format: str = Form("wav"),
    sample_rate: int = Form(16000),
    channels: int = Form(1)
):
    """
    Эндпоинт для конвертации видео в аудио
    
    Args:
        file: Загружаемый видео файл
        task_id: ID задачи
        audio_format: Формат выходного аудио (wav, mp3, flac)
        sample_rate: Частота дискретизации
        channels: Количество каналов
        
    Returns:
        JSON с результатами конвертации
    """
    
    logger.info(f"📤 Received video file for conversion: {file.filename} (task_id: {task_id})")
    
    # Проверка формата файла
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.VIDEO_FORMATS:
        logger.error(f"❌ Unsupported video format: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format. Supported formats: {', '.join(settings.VIDEO_FORMATS)}"
        )
    
    try:
        # Сохранение загруженного файла
        file_path = settings.UPLOAD_DIR / file.filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"💾 Video file saved: {file_path}")
        
        # Проверяем, что это видео файл
        if not video_service.is_video_file(file_path):
            raise HTTPException(
                status_code=400,
                detail="File is not a supported video file"
            )
        
        # Получаем информацию о видео
        video_info = video_service.get_video_info(file_path)
        
        # Настройки аудио
        audio_settings = {
            'sample_rate': sample_rate,
            'channels': channels,
            'format': audio_format,
            'codec': 'pcm_s16le' if audio_format == 'wav' else 'mp3'
        }
        
        # Конвертация в аудио
        output_filename = f"{task_id}_audio.{audio_format}"
        output_path = settings.OUTPUT_DIR / output_filename
        
        logger.info(f"🎬 Starting video to audio conversion...")
        
        audio_file = video_service.convert_to_audio(
            video_path=file_path,
            output_path=output_path,
            audio_settings=audio_settings
        )
        
        # Получаем информацию о созданном аудио файле
        audio_size = audio_file.stat().st_size / 1024  # KB
        
        logger.info(f"✅ Video successfully converted to audio: {audio_file}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "input_file": file.filename,
                "output_file": output_filename,
                "video_info": video_info,
                "audio_settings": audio_settings,
                "audio_file_size_kb": audio_size,
                "output_path": str(audio_file)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Video conversion error for task {task_id}: {e}")
        
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
                "message": f"Video conversion failed: {str(e)}"
            }
        )


@app.post("/convert/batch")
async def convert_batch(
    files: list[UploadFile] = File(...),
    task_id: str = Form(...),
    audio_format: str = Form("wav"),
    sample_rate: int = Form(16000),
    channels: int = Form(1)
):
    """
    Эндпоинт для пакетной конвертации видео в аудио
    
    Args:
        files: Список загружаемых видео файлов
        task_id: ID задачи
        audio_format: Формат выходного аудио
        sample_rate: Частота дискретизации
        channels: Количество каналов
        
    Returns:
        JSON с результатами конвертации
    """
    
    logger.info(f"📤 Received batch conversion request: {len(files)} files (task_id: {task_id})")
    
    results = []
    errors = []
    
    # Настройки аудио
    audio_settings = {
        'sample_rate': sample_rate,
        'channels': channels,
        'format': audio_format,
        'codec': 'pcm_s16le' if audio_format == 'wav' else 'mp3'
    }
    
    try:
        for i, file in enumerate(files):
            try:
                # Проверка формата файла
                file_extension = Path(file.filename).suffix.lower()
                if file_extension not in settings.VIDEO_FORMATS:
                    errors.append({
                        "filename": file.filename,
                        "error": f"Unsupported video format: {file_extension}"
                    })
                    continue
                
                # Сохранение файла
                file_path = settings.UPLOAD_DIR / f"{task_id}_{i}_{file.filename}"
                
                async with aiofiles.open(file_path, 'wb') as f:
                    content = await file.read()
                    await f.write(content)
                
                # Проверка видео файла
                if not video_service.is_video_file(file_path):
                    errors.append({
                        "filename": file.filename,
                        "error": "File is not a supported video file"
                    })
                    continue
                
                # Получаем информацию о видео
                video_info = video_service.get_video_info(file_path)
                
                # Конвертация
                logger.info(f"🎬 Converting file {i+1}/{len(files)}: {file.filename}")
                
                output_filename = f"{task_id}_{i}_audio.{audio_format}"
                output_path = settings.OUTPUT_DIR / output_filename
                
                audio_file = video_service.convert_to_audio(
                    video_path=file_path,
                    output_path=output_path,
                    audio_settings=audio_settings
                )
                
                audio_size = audio_file.stat().st_size / 1024  # KB
                
                results.append({
                    "filename": file.filename,
                    "task_id": f"{task_id}_{i}",
                    "output_file": output_filename,
                    "video_info": video_info,
                    "audio_file_size_kb": audio_size,
                    "output_path": str(audio_file)
                })
                
                logger.info(f"✅ File {i+1}/{len(files)} converted successfully")
                
            except Exception as e:
                logger.error(f"❌ Error converting file {file.filename}: {e}")
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
                "audio_settings": audio_settings,
                "results": results,
                "errors": errors
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Batch conversion error for task {task_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "task_id": task_id,
                "message": f"Batch conversion failed: {str(e)}"
            }
        )


@app.get("/formats")
async def get_supported_formats():
    """Получение информации о поддерживаемых форматах"""
    try:
        return JSONResponse(
            status_code=200,
            content={
                "supported_video_formats": list(video_service.VIDEO_FORMATS),
                "supported_audio_formats": list(video_service.AUDIO_FORMATS),
                "optimal_audio_settings": video_service.OPTIMAL_AUDIO_SETTINGS
            }
        )
    except Exception as e:
        logger.error(f"❌ Error getting formats info: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Скачивание сконвертированного аудио файла"""
    try:
        file_path = settings.OUTPUT_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File {filename} not found"
            )
        
        logger.info(f"📥 Downloading file: {filename}")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="audio/wav"  # Будет автоматически определен по расширению
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading file {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading file: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.features.video_to_audio.microservice:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info"
    )
