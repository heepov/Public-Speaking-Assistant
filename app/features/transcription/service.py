"""
Сервис транскрипции с использованием WhisperX
"""

import os
import torch
import whisperx
import librosa
import numpy as np
from pathlib import Path
from typing import Optional, Callable, Dict, List, Any
from datetime import datetime
import tempfile
import gc
import subprocess

from app.core.logger import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)


class TranscriptionService:
    """Основной сервис для транскрипции аудио файлов"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.model = None
        self.align_model = None
        self.diarize_model = None
        self.device = None
        self.compute_type = None
        
        # Настройки модели
        self.model_size = "base"  # tiny, base, small, medium, large-v2, large-v3
        self.language = "ru"      # Русский язык
        
        # Настройки обнаружения пауз
        self.pause_settings = {
            'min_pause_duration': 0.2,  # Минимальная длительность паузы (сек)
            'energy_threshold': 0.005,  # Порог энергии для детекции речи
            'frame_length': 1024,       # Длина кадра для анализа
            'hop_length': 256          # Шаг между кадрами
        }
    
    def convert_video_to_audio(self, video_path: Path, output_path: Path) -> bool:
        """Конвертация видео в аудио с помощью ffmpeg"""
        try:
            logger.info(f"🎬 Конвертируем видео в аудио: {video_path}")
            
            # Команда ffmpeg для конвертации
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',  # Без видео
                '-acodec', 'pcm_s16le',  # Кодек аудио
                '-ar', '16000',  # Частота дискретизации
                '-ac', '1',  # Моно
                '-y',  # Перезаписать файл
                str(output_path)
            ]
            
            # Выполняем команду
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 минут таймаут
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Видео успешно конвертировано в аудио: {output_path}")
                return True
            else:
                logger.error(f"❌ Ошибка конвертации видео: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Таймаут при конвертации видео")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при конвертации видео: {e}")
            return False

    def is_video_file(self, file_path: Path) -> bool:
        """Проверка, является ли файл видео"""
        return file_path.suffix.lower() in settings.VIDEO_FORMATS
    
    async def initialize(self):
        """Инициализация моделей и устройств"""
        logger.info("🚀 Инициализация сервиса транскрипции...")
        
        # Определяем устройство и тип вычислений
        self._setup_device()
        
        # Загружаем модель Whisper
        await self._load_whisper_model()
        
        # Загружаем модель для выравнивания
        await self._load_alignment_model()
        
        logger.info("✅ Сервис транскрипции успешно инициализирован")
    
    def _setup_device(self):
        """Настройка устройства для вычислений"""
        # Принудительно используем CPU для WhisperX
        self.device = "cpu"
        self.compute_type = "int8"
        
        # Отключаем CUDA для PyTorch
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        if torch.cuda.is_available():
            # Информация о GPU
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            logger.info(f"ℹ️ GPU доступен: {gpu_name} ({gpu_memory:.1f} ГБ), но принудительно используется CPU")
            
            # Очищаем кэш GPU
            torch.cuda.empty_cache()
            
        else:
            logger.info("ℹ️ CUDA недоступна, используется CPU")
        
        logger.info(f"🖥️ Устройство для транскрипции: {self.device.upper()}")
        logger.info(f"⚙️ Тип вычислений: {self.compute_type}")
    
    async def _load_whisper_model(self):
        """Загрузка модели WhisperX на CPU"""
        logger.info(f"📥 Загружаем модель Whisper на CPU: {self.model_size}")
        
        try:
            # Принудительно загружаем модель на CPU
            self.model = whisperx.load_model(
                self.model_size,
                device="cpu",  # Принудительно CPU
                compute_type="int8",  # Оптимизация для CPU
                language=self.language
            )
            
            logger.info(f"✅ Модель Whisper {self.model_size} загружена на CPU")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели Whisper: {e}")
            raise RuntimeError(f"Не удалось загрузить модель Whisper: {e}")
    
    async def _load_alignment_model(self):
        """Загрузка модели для выравнивания слов на CPU"""
        logger.info("📥 Загружаем модель для выравнивания слов на CPU...")
        
        try:
            # Пробуем загрузить модель для русского языка на CPU
            self.align_model, metadata = whisperx.load_align_model(
                language_code=self.language,
                device="cpu"  # Принудительно CPU
            )
            
            logger.info("✅ Модель выравнивания загружена на CPU")
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить модель выравнивания для русского языка: {e}")
            
            try:
                # Пробуем загрузить универсальную модель на CPU
                logger.info("🔄 Пробуем загрузить универсальную модель выравнивания на CPU...")
                self.align_model, metadata = whisperx.load_align_model(
                    language_code="en",  # Используем английскую модель как fallback
                    device="cpu"  # Принудительно CPU
                )
                logger.info("✅ Универсальная модель выравнивания загружена на CPU")
                
            except Exception as e2:
                logger.warning(f"⚠️ Не удалось загрузить универсальную модель выравнивания: {e2}")
                self.align_model = None
    
    def is_cuda_available(self) -> bool:
        """Проверка доступности CUDA"""
        return torch.cuda.is_available()
    
    def get_device_info(self) -> dict:
        """Получение информации об устройстве"""
        info = {
            "device": self.device,
            "compute_type": self.compute_type,
            "cuda_available": torch.cuda.is_available()
        }
        
        if torch.cuda.is_available():
            info.update({
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_total": torch.cuda.get_device_properties(0).total_memory,
                "gpu_memory_allocated": torch.cuda.memory_allocated(0),
                "gpu_memory_cached": torch.cuda.memory_reserved(0)
            })
        
        return info
    
    def _detect_pauses(
        self,
        audio_path: Path,
        log_callback: Optional[Callable[[str, str], None]] = None
    ) -> List[Dict]:
        """
        Обнаружение пауз в аудио файле
        
        Args:
            audio_path: Путь к аудио файлу
            log_callback: Функция для логирования
            
        Returns:
            Список словарей с информацией о паузах
        """
        
        def log(level: str, message: str):
            if log_callback:
                log_callback(level, message)
            logger.debug(message)
        
        log("INFO", "🔍 Анализируем паузы в аудио...")
        
        try:
            # Загружаем аудио
            y, sr = librosa.load(str(audio_path), sr=None)
            
            # Вычисляем энергию сигнала
            frame_length = self.pause_settings['frame_length']
            hop_length = self.pause_settings['hop_length']
            
            # RMS энергия
            rms = librosa.feature.rms(
                y=y,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # Времена кадров
            times = librosa.frames_to_time(
                range(len(rms)),
                sr=sr,
                hop_length=hop_length
            )
            
            # Определяем пороговое значение
            threshold = self.pause_settings['energy_threshold']
            
            # Находим участки с низкой энергией (паузы)
            is_pause = rms < threshold
            
            # Группируем соседние паузы
            pauses = []
            pause_start = None
            
            for i, (time, pause) in enumerate(zip(times, is_pause)):
                if pause and pause_start is None:
                    # Начало паузы
                    pause_start = time
                elif not pause and pause_start is not None:
                    # Конец паузы
                    pause_duration = time - pause_start
                    
                    if pause_duration >= self.pause_settings['min_pause_duration']:
                        pauses.append({
                            'start': pause_start,
                            'end': time,
                            'duration': pause_duration
                        })
                    
                    pause_start = None
            
            # Проверяем последнюю паузу
            if pause_start is not None:
                pause_duration = times[-1] - pause_start
                if pause_duration >= self.pause_settings['min_pause_duration']:
                    pauses.append({
                        'start': pause_start,
                        'end': times[-1],
                        'duration': pause_duration
                    })
            
            log("INFO", f"🔍 Обнаружено пауз: {len(pauses)}")
            
            return pauses
            
        except Exception as e:
            log("WARNING", f"⚠️ Ошибка при анализе пауз: {e}")
            return []
    
    async def transcribe_file(
        self,
        file_path: Path,
        file_extension: str,
        task_id: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        log_callback: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, str]:
        """
        Транскрибция аудио/видео файла
        
        Args:
            file_path: Путь к файлу
            file_extension: Расширение файла
            task_id: ID задачи
            progress_callback: Функция обновления прогресса
            log_callback: Функция логирования
            
        Returns:
            Форматированный текст транскрипции
        """
        
        def log(level: str, message: str):
            if log_callback:
                log_callback(level, message)
            logger.info(message)
        
        def update_progress(percent: int, message: str):
            if progress_callback:
                progress_callback(percent, message)
        
        log("INFO", f"🎤 Начинаем транскрипцию файла: {file_path.name}")
        
        # Переменные для очистки
        audio_file_path = None
        temp_audio_path = None
        
        try:
            update_progress(10, "Подготовка аудио...")
            
            # Конвертируем в аудио если необходимо
            if file_extension.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                log("INFO", "📹 Конвертируем видео в аудио...")
                
                temp_audio_path = Path(tempfile.mkstemp(suffix=".wav")[1])
                if not self.convert_video_to_audio(file_path, temp_audio_path):
                    raise RuntimeError("Не удалось конвертировать видео в аудио.")
                audio_file_path = temp_audio_path
                
            else:
                log("INFO", "🎵 Используем исходный аудио файл")
                audio_file_path = file_path
            
            update_progress(35, "Анализируем пауз...")
            
            # Анализ пауз
            pauses = self._detect_pauses(audio_file_path, log_callback)
            
            update_progress(40, "Загружаем аудио в Whisper...")
            
            # Загружаем аудио для Whisper
            audio = whisperx.load_audio(str(audio_file_path))
            
            update_progress(50, "Выполняем транскрипцию...")
            
            # Основная транскрипция
            log("INFO", f"🎯 Выполняем транскрипцию (модель: {self.model_size}, устройство: {self.device})")
            
            result = self.model.transcribe(
                audio,
                batch_size=16 if self.device == "cuda" else 4
            )
            
            update_progress(75, "Выравниваем слова...")
            
            # Выравнивание слов (если модель доступна)
            if self.align_model is not None:
                try:
                    log("INFO", "🎯 Выравниваем слова по временным меткам...")
                    
                    result = whisperx.align(
                        result["segments"],
                        self.align_model,
                        whisperx.utils.get_writer_output_format("json"),
                        audio,
                        "cpu",  # Принудительно CPU
                        return_char_alignments=False
                    )
                    
                    log("INFO", "✅ Выравнивание слов завершено успешно")
                    
                except Exception as e:
                    log("WARNING", f"⚠️ Ошибка выравнивания: {e}")
                    # Создаем простую разбивку по словам на основе сегментов
                    log("INFO", "🔄 Создаем простую разбивку по словам...")
                    result = self._create_simple_word_alignment(result)
            else:
                log("INFO", "🔄 Модель выравнивания недоступна, создаем простую разбивку по словам...")
                result = self._create_simple_word_alignment(result)
            
            update_progress(90, "Форматируем результат...")
            
            # Форматируем результат
            formatted_results = self._format_transcription_result(
                result,
                pauses,
                file_path.name,
                task_id
            )
            
            update_progress(100, "Транскрипция завершена!")
            
            log("INFO", "✅ Транскрипция успешно завершена")
            
            return formatted_results
            
        except Exception as e:
            log("ERROR", f"❌ Ошибка транскрипции: {e}")
            raise RuntimeError(f"Ошибка транскрипции: {e}")
            
        finally:
            # Очистка временных файлов
            if temp_audio_path and temp_audio_path.exists():
                try:
                    temp_audio_path.unlink()
                    log("INFO", "🗑️ Временный аудио файл удален")
                except Exception as e:
                    log("WARNING", f"⚠️ Не удалось удалить временный файл: {e}")
            
            # Очистка GPU памяти
            if self.device == "cuda":
                torch.cuda.empty_cache()
                gc.collect()
    
    def _create_simple_word_alignment(self, result: Dict) -> Dict:
        """
        Создание простой разбивки по словам на основе сегментов
        
        Args:
            result: Результат транскрипции от Whisper
            
        Returns:
            Результат с добавленной разбивкой по словам
        """
        
        segments = result.get("segments", [])
        
        for segment in segments:
            text = segment.get('text', '').strip()
            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            
            # Разбиваем текст на слова, сохраняя знаки препинания
            import re
            words = re.findall(r'\b\w+\b|[^\w\s]', text)
            if not words:
                continue
            
            # Вычисляем примерное время для каждого слова
            total_duration = end_time - start_time
            
            # Учитываем, что знаки препинания произносятся быстрее
            word_durations = []
            for word in words:
                if re.match(r'[^\w\s]', word):  # Знак препинания
                    word_durations.append(0.1)  # Короткая пауза для знаков препинания
                else:
                    # Примерная длительность слова (0.3-0.8 секунды)
                    word_durations.append(0.5)
            
            # Нормализуем длительности, чтобы они соответствовали общей длительности сегмента
            total_word_duration = sum(word_durations)
            if total_word_duration > 0:
                scale_factor = total_duration / total_word_duration
                word_durations = [d * scale_factor for d in word_durations]
            
            # Создаем список слов с временными метками
            word_list = []
            current_time = start_time
            
            for i, word in enumerate(words):
                word_end_time = current_time + word_durations[i]
                
                word_list.append({
                    'word': word,
                    'start': current_time,
                    'end': word_end_time
                })
                
                current_time = word_end_time
            
            # Добавляем разбивку по словам в сегмент
            segment['words'] = word_list
        
        return result
    
    def _format_transcription_result(
        self,
        whisper_result: Dict,
        pauses: List[Dict],
        filename: str,
        task_id: str
    ) -> Dict[str, str]:
        """
        Форматирование результата транскрипции в два отдельных файла
        
        Args:
            whisper_result: Результат от WhisperX
            pauses: Список пауз
            filename: Имя исходного файла
            task_id: ID задачи
            
        Returns:
            Словарь с двумя отформатированными текстами: 'simple_text' и 'detailed_text'
        """
        
        segments = whisper_result.get("segments", [])
        
        # 1. Простой текст (только полный текст)
        simple_lines = []
        simple_lines.append("ТРАНСКРИПЦИЯ ВИДЕО")
        simple_lines.append("=" * 50)
        simple_lines.append("")
        
        # Метаданные
        simple_lines.append(f"Файл: {filename}")
        simple_lines.append(f"Модель: {self.model_size}")
        simple_lines.append(f"Устройство: {self.device}")
        simple_lines.append(f"Язык: {self.language}")
        simple_lines.append(f"Время обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        simple_lines.append("")
        
        # Полный текст
        simple_lines.append("ПОЛНЫЙ ТЕКСТ:")
        simple_lines.append("-" * 20)
        
        full_text = " ".join(
            segment.get('text', '').strip()
            for segment in segments
        ).strip()
        
        simple_lines.append(full_text)
        
        # 2. Детальный текст (с временными метками и паузами)
        detailed_lines = []
        detailed_lines.append("ТРАНСКРИПЦИЯ ВИДЕО (ДЕТАЛЬНАЯ)")
        detailed_lines.append("=" * 50)
        detailed_lines.append("")
        
        # Метаданные
        detailed_lines.append(f"Файл: {filename}")
        detailed_lines.append(f"Модель: {self.model_size}")
        detailed_lines.append(f"Устройство: {self.device}")
        detailed_lines.append(f"Язык: {self.language}")
        detailed_lines.append(f"Время обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        detailed_lines.append(f"Обнаружено пауз: {len(pauses)}")
        detailed_lines.append("")
        
        # Список пауз
        if pauses:
            detailed_lines.append("ОБНАРУЖЕННЫЕ ПАУЗЫ:")
            detailed_lines.append("-" * 30)
            
            for i, pause in enumerate(pauses, 1):
                start_time = self._format_time(pause['start'])
                end_time = self._format_time(pause['end'])
                duration = pause['duration']
                
                detailed_lines.append(f"Пауза {i}: [{start_time} - {end_time}] (длительность: {duration:.2f}с)")
            
            detailed_lines.append("")
        
        # Детальная разбивка по словам (если доступна)
        has_word_timestamps = any(
            'words' in segment and segment['words']
            for segment in segments
        )
        
        if has_word_timestamps:
            detailed_lines.append("ДЕТАЛЬНАЯ РАЗБИВКА ПО СЛОВАМ:")
            detailed_lines.append("-" * 40)
            
            for segment in segments:
                words = segment.get('words', [])
                
                for word_info in words:
                    start_time = self._format_time(word_info.get('start', 0))
                    end_time = self._format_time(word_info.get('end', 0))
                    word = word_info.get('word', '').strip()
                    
                    detailed_lines.append(f"  [{start_time} - {end_time}] {word}")
            
            detailed_lines.append("")
        else:
            # Если нет детальных временных меток слов, показываем сегменты
            if segments:
                detailed_lines.append("СЕГМЕНТЫ:")
                detailed_lines.append("-" * 20)
                
                for segment in segments:
                    start_time = self._format_time(segment.get('start', 0))
                    end_time = self._format_time(segment.get('end', 0))
                    text = segment.get('text', '').strip()
                    
                    detailed_lines.append(f"[{start_time} - {end_time}] {text}")
                
                detailed_lines.append("")
        
        # Полный текст в детальном файле тоже
        detailed_lines.append("ПОЛНЫЙ ТЕКСТ:")
        detailed_lines.append("-" * 20)
        detailed_lines.append(full_text)
        
        return {
            'simple_text': "\n".join(simple_lines),
            'detailed_text': "\n".join(detailed_lines)
        }
    
    def _format_time(self, seconds: float) -> str:
        """
        Форматирование времени в MM:SS.ss формат
        
        Args:
            seconds: Время в секундах
            
        Returns:
            Отформатированная строка времени
        """
        
        minutes = int(seconds // 60)
        secs = seconds % 60
        
        return f"{minutes:02d}:{secs:05.2f}"
