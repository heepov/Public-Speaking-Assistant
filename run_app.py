#!/usr/bin/env python3
"""
Точка входа для запуска приложения обработки медиа файлов
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Импортируем и запускаем приложение
from app.main import app
import uvicorn
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)

if __name__ == "__main__":
    logger.info("🎬 Запуск приложения обработки медиа файлов...")
    
    # Получаем настройки из переменных окружения
    host = settings.HOST
    port = settings.PORT
    log_level = settings.LOG_LEVEL
    
    # В Docker используем 0.0.0.0 для доступа извне
    if settings.DOCKER_ENV:
        host = "0.0.0.0"
    
    logger.info(f"🌐 Сервер запускается на {host}:{port}")
    logger.info(f"📊 Уровень логирования: {log_level}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,  # Отключаем reload в Docker
        log_level=log_level
    )
