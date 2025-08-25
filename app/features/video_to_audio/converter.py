"""
Конвертер видео в аудио с использованием FFmpeg
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import ffmpeg

from app.core.logger import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)


class VideoToAudioConverter:
    """Класс для конвертации видео в аудио"""
    
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
        """Инициализация конвертера"""
        self.ffmpeg_path = self._check_ffmpeg_installation()
    
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
        
        ffmpeg_found = False
        
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
                    logger.info(f"✅ FFmpeg найден: {version_info}")
                    logger.info(f"📍 Путь: {ffmpeg_path}")
                    ffmpeg_found = True
                    break
                    
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not ffmpeg_found:
            logger.error("❌ FFmpeg не найден в системе")
            logger.error("🔍 Проверенные пути:")
            for path in ffmpeg_paths:
                logger.error(f"   - {path}")
            raise RuntimeError(
                "FFmpeg не установлен. Установите FFmpeg:\n"
                "Windows: choco install ffmpeg или скачайте с https://ffmpeg.org/\n"
                "Или добавьте FFmpeg в PATH"
            )
        
        return ffmpeg_path
    
    def is_video_file(self, file_path: Path) -> bool:
        """
        Проверка, является ли файл видео
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если файл видео, False если аудио
        """
        return file_path.suffix.lower() in self.VIDEO_FORMATS
    
    def is_audio_file(self, file_path: Path) -> bool:
        """
        Проверка, является ли файл аудио
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если файл аудио
        """
        return file_path.suffix.lower() in self.AUDIO_FORMATS
    
    def get_media_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Получение информации о медиа файле
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Словарь с информацией о файле
        """
        logger.info(f"📊 Получаем информацию о файле: {file_path.name}")
        
        try:
            # Используем ffmpeg.probe без указания cmd - он сам найдет ffprobe
            probe = ffmpeg.probe(str(file_path))
            
            # Общая информация
            format_info = probe.get('format', {})
            duration = float(format_info.get('duration', 0))
            file_size = int(format_info.get('size', 0))
            
            # Информация о потоках
            streams = probe.get('streams', [])
            
            video_streams = [s for s in streams if s.get('codec_type') == 'video']
            audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
            
            info = {
                'duration': duration,
                'file_size': file_size,
                'format_name': format_info.get('format_name', 'unknown'),
                'video_streams': len(video_streams),
                'audio_streams': len(audio_streams),
                'has_video': len(video_streams) > 0,
                'has_audio': len(audio_streams) > 0
            }
            
            # Детальная информация об аудио потоке
            if audio_streams:
                audio_stream = audio_streams[0]
                info.update({
                    'audio_codec': audio_stream.get('codec_name', 'unknown'),
                    'audio_sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'audio_channels': int(audio_stream.get('channels', 0)),
                    'audio_bit_rate': int(audio_stream.get('bit_rate', 0))
                })
            
            # Детальная информация о видео потоке
            if video_streams:
                video_stream = video_streams[0]
                info.update({
                    'video_codec': video_stream.get('codec_name', 'unknown'),
                    'video_width': int(video_stream.get('width', 0)),
                    'video_height': int(video_stream.get('height', 0)),
                    'video_fps': eval(video_stream.get('r_frame_rate', '0/1'))
                })
            
            logger.info(f"📋 Информация о файле: {info}")
            return info
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении информации о файле: {e}")
            raise RuntimeError(f"Не удалось получить информацию о файле: {e}")
    
    def convert_to_audio(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        log_callback: Optional[Callable[[str, str], None]] = None
    ) -> Path:
        """
        Конвертация видео в аудио или оптимизация аудио файла
        
        Args:
            input_path: Путь к исходному файлу
            output_path: Путь для сохранения (если None - создается временный)
            progress_callback: Функция для обновления прогресса
            log_callback: Функция для логирования
            
        Returns:
            Путь к сконвертированному аудио файлу
        """
        
        def log(level: str, message: str):
            if log_callback:
                log_callback(level, message)
            logger.info(message)
        
        def update_progress(percent: int, message: str):
            if progress_callback:
                progress_callback(percent, message)
        
        log("INFO", f"🎵 Начинаем конвертацию: {input_path.name}")
        
        # Получаем информацию о файле
        try:
            media_info = self.get_media_info(input_path)
        except Exception as e:
            log("ERROR", f"Ошибка при анализе файла: {e}")
            raise
        
        # Проверяем наличие аудио потока
        if not media_info['has_audio']:
            raise RuntimeError("Файл не содержит аудио потока")
        
        # Определяем выходной файл
        if output_path is None:
            # Создаем файл в папке outputs с уникальным именем
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            output_path = settings.OUTPUT_DIR / f"converted_audio_{unique_id}.wav"
        
        log("INFO", f"💾 Выходной файл: {output_path}")
        
        update_progress(10, "Подготовка к конвертации...")
        
        try:
            # Настраиваем входной поток (ffmpeg-python сам найдет ffmpeg)
            input_stream = ffmpeg.input(str(input_path))
            
            # Настраиваем выходные параметры
            output_kwargs = {
                'acodec': self.OPTIMAL_AUDIO_SETTINGS['codec'],
                'ar': self.OPTIMAL_AUDIO_SETTINGS['sample_rate'],
                'ac': self.OPTIMAL_AUDIO_SETTINGS['channels'],
                'f': self.OPTIMAL_AUDIO_SETTINGS['format']
            }
            
            # Если это видео файл - извлекаем только аудио
            if media_info['has_video']:
                log("INFO", "📹 Извлекаем аудио из видео файла")
                output_stream = ffmpeg.output(
                    input_stream.audio,
                    str(output_path),
                    **output_kwargs
                )
            else:
                log("INFO", "🎵 Оптимизируем аудио файл для транскрипции")
                output_stream = ffmpeg.output(
                    input_stream,
                    str(output_path),
                    **output_kwargs
                )
            
            update_progress(20, "Запуск конвертации...")
            
            # Запускаем конвертацию с детальным логированием
            process = ffmpeg.run_async(
                output_stream,
                pipe_stderr=True,
                overwrite_output=True,
                quiet=False
            )
            
            # Мониторим прогресс
            duration = media_info['duration']
            last_progress = 20
            
            while True:
                output = process.stderr.readline()
                if output == b'' and process.poll() is not None:
                    break
                
                if output:
                    line = output.decode('utf-8', errors='ignore').strip()
                    
                    # Парсим прогресс из вывода FFmpeg
                    if 'time=' in line and duration > 0:
                        try:
                            time_str = line.split('time=')[1].split()[0]
                            # Конвертируем время в секунды
                            time_parts = time_str.split(':')
                            if len(time_parts) == 3:
                                current_time = (
                                    float(time_parts[0]) * 3600 +
                                    float(time_parts[1]) * 60 +
                                    float(time_parts[2])
                                )
                                
                                # Вычисляем прогресс (от 20% до 90%)
                                progress = min(90, 20 + int((current_time / duration) * 70))
                                
                                if progress > last_progress:
                                    update_progress(
                                        progress,
                                        f"Конвертация: {current_time:.1f}s / {duration:.1f}s"
                                    )
                                    last_progress = progress
                        except:
                            pass  # Игнорируем ошибки парсинга
                    
                    # Логируем важные сообщения
                    if any(keyword in line.lower() for keyword in ['error', 'warning']):
                        log("WARNING", f"FFmpeg: {line}")
            
            # Ждем завершения процесса
            return_code = process.wait()
            
            if return_code != 0:
                stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
                log("ERROR", f"FFmpeg завершился с ошибкой (код {return_code}): {stderr_output}")
                raise RuntimeError(f"Ошибка конвертации (код {return_code})")
            
            update_progress(95, "Проверка результата...")
            
            # Проверяем, что файл создался и не пустой
            if not output_path.exists():
                raise RuntimeError("Выходной файл не был создан")
            
            output_size = output_path.stat().st_size
            if output_size == 0:
                raise RuntimeError("Выходной файл пустой")
            
            # Получаем информацию о результате
            result_info = self.get_media_info(output_path)
            
            log("INFO", f"✅ Конвертация завершена успешно:")
            log("INFO", f"   📄 Размер файла: {output_size / (1024*1024):.2f} МБ")
            log("INFO", f"   🎵 Длительность: {result_info['duration']:.2f} сек")
            log("INFO", f"   📊 Частота: {result_info.get('audio_sample_rate', 'N/A')} Гц")
            log("INFO", f"   🔊 Каналы: {result_info.get('audio_channels', 'N/A')}")
            
            update_progress(100, "Конвертация завершена!")
            
            return output_path
            
        except Exception as e:
            log("ERROR", f"❌ Ошибка при конвертации: {e}")
            
            # Удаляем частично созданный файл
            if output_path and output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            
            raise RuntimeError(f"Ошибка конвертации: {e}")
    
    def cleanup_temp_file(self, file_path: Path):
        """
        Очистка временного файла (отключено для сохранения файлов)
        
        Args:
            file_path: Путь к временному файлу
        """
        try:
            if file_path.exists():
                logger.info(f"💾 Временный файл сохранен: {file_path.name}")
                logger.info(f"📍 Путь к файлу: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить информацию о файле {file_path}: {e}")
