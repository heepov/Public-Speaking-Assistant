"""
Сервис конвертации видео в аудио с использованием FFmpeg
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import ffmpeg

from app.core.logger import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)


class VideoToAudioService:
    """Сервис для конвертации видео в аудио"""
    
    # Используем настройки из конфигурации
    VIDEO_FORMATS = settings.VIDEO_FORMATS
    AUDIO_FORMATS = settings.SUPPORTED_AUDIO_FORMATS
    
    # Оптимальные настройки для транскрипции
    OPTIMAL_AUDIO_SETTINGS = {
        'sample_rate': 16000,    # WhisperX работает лучше с 16kHz
        'channels': 1,           # Моно канал
        'format': 'wav',         # WAV для лучшего качества
        'codec': 'pcm_s16le'     # 16-bit PCM
    }
    
    def __init__(self):
        """Инициализация сервиса"""
        self.ffmpeg_path = None
        self.is_initialized = False
    
    async def initialize(self):
        """Инициализация сервиса"""
        try:
            logger.info("🚀 Initializing video to audio service...")
            
            # Проверка установки FFmpeg
            self.ffmpeg_path = self._check_ffmpeg_installation()
            
            self.is_initialized = True
            logger.info("✅ Video to audio service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing video to audio service: {e}")
            raise
    
    def _check_ffmpeg_installation(self) -> str:
        """Проверка установки FFmpeg"""
        import os
        
        # Список возможных путей к FFmpeg (кроссплатформенный)
        ffmpeg_paths = [
            'ffmpeg',  # В PATH (основной вариант для Docker/Linux)
            '/usr/bin/ffmpeg',  # Стандартный путь в Linux
            '/usr/local/bin/ffmpeg',  # Альтернативный путь в Linux
        ]
        
        # Добавляем Windows пути только если мы на Windows
        if os.name == 'nt':
            ffmpeg_paths.extend([
                r'C:\Users\developer\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe',
                r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
                r'C:\ffmpeg\bin\ffmpeg.exe'
            ])
        
        for ffmpeg_path in ffmpeg_paths:
            try:
                result = subprocess.run(
                    [ffmpeg_path, '-version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version_info = result.stdout.split('\n')[0]
                    logger.info(f"✅ FFmpeg found: {version_info} at {ffmpeg_path}")
                    return ffmpeg_path
                    
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        logger.error("❌ FFmpeg not found in system")
        raise RuntimeError(
            "FFmpeg не установлен. Установите FFmpeg:\n"
            "Windows: choco install ffmpeg или скачайте с https://ffmpeg.org/\n"
            "Или добавьте FFmpeg в PATH"
        )
    
    def is_video_file(self, file_path: Path) -> bool:
        """
        Проверка, является ли файл видео
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если файл является видео
        """
        if not file_path.exists():
            return False
        
        file_extension = file_path.suffix.lower()
        return file_extension in self.VIDEO_FORMATS
    
    def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """
        Получение информации о видео файле
        
        Args:
            video_path: Путь к видео файлу
            
        Returns:
            Словарь с информацией о видео
        """
        try:
            logger.info(f"📹 Getting video info: {video_path}")
            
            # Используем ffprobe для получения информации
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                
                # Извлекаем основную информацию
                video_info = {
                    'duration': float(info.get('format', {}).get('duration', 0)),
                    'size': int(info.get('format', {}).get('size', 0)),
                    'bitrate': int(info.get('format', {}).get('bit_rate', 0)),
                    'format': info.get('format', {}).get('format_name', ''),
                    'streams': len(info.get('streams', []))
                }
                
                logger.info(f"✅ Video info retrieved: {video_info['duration']:.2f}s, {video_info['size']} bytes")
                return video_info
                
            else:
                logger.error(f"❌ Error getting video info: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error getting video info: {e}")
            return {}
    
    def convert_to_audio(
        self, 
        video_path: Path, 
        output_path: Path,
        audio_settings: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Конвертация видео в аудио
        
        Args:
            video_path: Путь к видео файлу
            output_path: Путь для сохранения аудио файла
            audio_settings: Настройки аудио (опционально)
            
        Returns:
            Путь к созданному аудио файлу
        """
        if not self.is_initialized:
            raise RuntimeError("Service not initialized. Call initialize() first.")
        
        if not self.is_video_file(video_path):
            raise ValueError(f"File is not a supported video format: {video_path}")
        
        # Используем настройки по умолчанию если не указаны
        if audio_settings is None:
            audio_settings = self.OPTIMAL_AUDIO_SETTINGS
        
        try:
            logger.info(f"🎬 Converting video to audio: {video_path}")
            logger.info(f"⚙️ Audio settings: {audio_settings}")
            
            # Создаем директорию для выходного файла если не существует
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Команда ffmpeg для конвертации
            cmd = [
                self.ffmpeg_path,
                '-i', str(video_path),
                '-vn',  # Без видео
                '-acodec', audio_settings['codec'],
                '-ar', str(audio_settings['sample_rate']),
                '-ac', str(audio_settings['channels']),
                '-f', audio_settings['format'],
                '-y',  # Перезаписать файл
                str(output_path)
            ]
            
            # Выполняем команду
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 минут таймаут
            )
            
            if result.returncode == 0:
                # Проверяем что файл создан и не пустой
                if output_path.exists() and output_path.stat().st_size > 0:
                    file_size = output_path.stat().st_size / 1024  # KB
                    logger.info(f"✅ Video successfully converted to audio: {output_path} ({file_size:.1f} KB)")
                    return output_path
                else:
                    raise RuntimeError("Output file is empty or not created")
            else:
                logger.error(f"❌ Video conversion error: {result.stderr}")
                raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout during video conversion")
            raise RuntimeError("Video conversion timeout")
        except Exception as e:
            logger.error(f"❌ Error during video conversion: {e}")
            raise
    
    def convert_to_audio_with_progress(
        self, 
        video_path: Path, 
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
        audio_settings: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Конвертация видео в аудио с отслеживанием прогресса
        
        Args:
            video_path: Путь к видео файлу
            output_path: Путь для сохранения аудио файла
            progress_callback: Функция для отслеживания прогресса
            audio_settings: Настройки аудио (опционально)
            
        Returns:
            Путь к созданному аудио файлу
        """
        if not self.is_initialized:
            raise RuntimeError("Service not initialized. Call initialize() first.")
        
        if not self.is_video_file(video_path):
            raise ValueError(f"File is not a supported video format: {video_path}")
        
        # Получаем информацию о видео для отслеживания прогресса
        video_info = self.get_video_info(video_path)
        total_duration = video_info.get('duration', 0)
        
        # Используем настройки по умолчанию если не указаны
        if audio_settings is None:
            audio_settings = self.OPTIMAL_AUDIO_SETTINGS
        
        try:
            logger.info(f"🎬 Converting video to audio with progress: {video_path}")
            
            # Создаем директорию для выходного файла если не существует
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Команда ffmpeg с выводом прогресса
            cmd = [
                self.ffmpeg_path,
                '-i', str(video_path),
                '-vn',  # Без видео
                '-acodec', audio_settings['codec'],
                '-ar', str(audio_settings['sample_rate']),
                '-ac', str(audio_settings['channels']),
                '-f', audio_settings['format'],
                '-progress', 'pipe:1',  # Вывод прогресса
                '-y',  # Перезаписать файл
                str(output_path)
            ]
            
            # Выполняем команду с отслеживанием прогресса
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Отслеживаем прогресс
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Парсим прогресс из вывода ffmpeg
                    if 'out_time_ms=' in output:
                        try:
                            time_ms = int(output.split('=')[1])
                            current_time = time_ms / 1000000  # конвертируем в секунды
                            if total_duration > 0 and progress_callback:
                                progress = min(current_time / total_duration, 1.0)
                                progress_callback(progress)
                        except (ValueError, IndexError):
                            pass
            
            # Ждем завершения процесса
            return_code = process.wait()
            
            if return_code == 0:
                # Проверяем что файл создан и не пустой
                if output_path.exists() and output_path.stat().st_size > 0:
                    file_size = output_path.stat().st_size / 1024  # KB
                    logger.info(f"✅ Video successfully converted to audio: {output_path} ({file_size:.1f} KB)")
                    return output_path
                else:
                    raise RuntimeError("Output file is empty or not created")
            else:
                stderr_output = process.stderr.read()
                logger.error(f"❌ Video conversion error: {stderr_output}")
                raise RuntimeError(f"FFmpeg conversion failed: {stderr_output}")
                
        except Exception as e:
            logger.error(f"❌ Error during video conversion: {e}")
            raise
    
    def cleanup_temp_file(self, file_path: Path):
        """
        Очистка временного файла (отключено для сохранения файлов)
        
        Args:
            file_path: Путь к временному файлу
        """
        try:
            if file_path.exists():
                logger.info(f"Temporary file saved: {file_path.name}")
                logger.info(f"File path: {file_path}")
        except Exception as e:
            logger.warning(f"Could not get file info for {file_path}: {e}")
