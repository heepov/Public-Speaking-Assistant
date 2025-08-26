"""
Конфигурация приложения
"""

import os
from pathlib import Path
from typing import Optional

class Settings:
    """Настройки приложения"""
    
    # Основные настройки
    APP_NAME: str = "Медиа Обработчик"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Настройки сервера
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Пути к директориям
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # В Docker среде используем другие пути
    if os.getenv("DOCKER_ENV", "false").lower() == "true":
        UPLOAD_DIR: Path = Path("/app/uploads")
        OUTPUT_DIR: Path = Path("/app/outputs")
        LOGS_DIR: Path = Path("/app/logs")
    
    # Настройки Docker
    DOCKER_ENV: bool = os.getenv("DOCKER_ENV", "false").lower() == "true"
    
    # Поддерживаемые форматы
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
    
    @property
    def ALL_SUPPORTED_FORMATS(self):
        return self.SUPPORTED_VIDEO_FORMATS | self.SUPPORTED_AUDIO_FORMATS
    
    @property
    def VIDEO_FORMATS(self):
        return self.SUPPORTED_VIDEO_FORMATS
    
    def create_directories(self):
        """Создание необходимых директорий"""
        directories = [self.UPLOAD_DIR, self.OUTPUT_DIR, self.LOGS_DIR]
        
        for directory in directories:
            try:
                directory.mkdir(exist_ok=True)
            except Exception as e:
                print(f"⚠️ Не удалось создать директорию {directory}: {e}")

# Глобальный экземпляр настроек
settings = Settings()
