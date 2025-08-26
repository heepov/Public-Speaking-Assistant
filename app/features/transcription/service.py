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
import json

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
        
        # Настройки кэширования моделей
        self._setup_model_cache()
        
        # Настройки обнаружения пауз
        self.pause_settings = {
            'min_pause_duration': 0.2,  # Минимальная длительность паузы (сек)
            'energy_threshold': 0.005,  # Порог энергии для детекции речи
            'frame_length': 1024,       # Длина кадра для анализа
            'hop_length': 256          # Шаг между кадрами
        }
    
    def _setup_model_cache(self):
        """Настройка кэширования моделей"""
        # Проверяем переменные окружения для кэширования
        cache_dir = os.getenv('WHISPERX_CACHE_DIR', '/app/app/features/transcription/models_cache')
        hf_home = os.getenv('HF_HOME', '/app/app/features/transcription/models_cache')
        transformers_cache = os.getenv('TRANSFORMERS_CACHE', '/app/app/features/transcription/models_cache')
        
        # Создаем директории кэша если они не существуют
        for cache_path in [cache_dir, hf_home, transformers_cache]:
            Path(cache_path).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Model cache directory: {cache_dir}")
        logger.info(f"📁 HuggingFace cache: {hf_home}")
        logger.info(f"📁 Transformers cache: {transformers_cache}")
    
    def is_audio_file(self, file_path: Path) -> bool:
        """Проверка, является ли файл аудио"""
        return file_path.suffix.lower() in settings.SUPPORTED_AUDIO_FORMATS
    
    async def initialize(self):
        """Инициализация моделей и устройств"""
        logger.info("🚀 Initializing transcription service...")
        
        # Определяем устройство и тип вычислений
        self._setup_device()
        
        # Загружаем модель Whisper
        await self._load_whisper_model()
        
        # Загружаем модель для выравнивания
        await self._load_alignment_model()
        
        logger.info("✅ Transcription service successfully initialized")
    
    def _setup_device(self):
        """Настройка устройства для вычислений"""
        # Автоматически определяем доступное устройство
        if torch.cuda.is_available():
            self.device = "cuda"
            self.compute_type = "float16"  # Оптимально для GPU
            
            # Информация о GPU
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            logger.info(f"🚀 GPU available: {gpu_name} ({gpu_memory:.1f} GB)")
            logger.info(f"🎯 Using GPU for transcription acceleration")
            
            # Очищаем кэш GPU
            torch.cuda.empty_cache()
            
        else:
            self.device = "cpu"
            self.compute_type = "int8"  # Оптимально для CPU
            logger.info("ℹ️ CUDA not available, using CPU")
        
        logger.info(f"🖥️ Transcription device: {self.device.upper()}")
        logger.info(f"⚙️ Compute type: {self.compute_type}")
    
    async def _load_whisper_model(self):
        """Загрузка модели WhisperX"""
        logger.info(f"📥 Loading Whisper model on {self.device.upper()}: {self.model_size}")
        
        try:
            # Получаем путь к кэшу моделей
            cache_dir = os.getenv('WHISPERX_CACHE_DIR', '/app/app/features/transcription/models_cache')
            
            # Загружаем модель на определенное устройство с использованием кэша
            self.model = whisperx.load_model(
                self.model_size,
                device=self.device,  # Используем определенное устройство
                compute_type=self.compute_type,  # Используем определенный тип вычислений
                language=self.language,
                download_root=cache_dir  # Используем кэш для загрузки
            )
            
            logger.info(f"✅ Whisper model {self.model_size} loaded on {self.device.upper()}")
            logger.info(f"📁 Model cached in: {cache_dir}")
            
        except Exception as e:
            logger.error(f"❌ Error loading Whisper model: {e}")
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    
    async def _load_alignment_model(self):
        """Загрузка модели для выравнивания слов"""
        logger.info(f"📥 Loading word alignment model on {self.device.upper()}...")
        
        try:
            # Получаем путь к кэшу моделей
            cache_dir = os.getenv('WHISPERX_CACHE_DIR', '/app/app/features/transcription/models_cache')
            
            # Пробуем загрузить модель для русского языка
            self.align_model, metadata = whisperx.load_align_model(
                language_code=self.language,
                device=self.device,  # Используем определенное устройство
                cache_dir=cache_dir  # Используем кэш для загрузки
            )
            
            logger.info(f"✅ Alignment model loaded on {self.device.upper()}")
            logger.info(f"📁 Alignment model cached in: {cache_dir}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load alignment model for Russian: {e}")
            
            try:
                # Пробуем загрузить универсальную модель
                logger.info(f"🔄 Trying to load universal alignment model on {self.device.upper()}...")
                self.align_model, metadata = whisperx.load_align_model(
                    language_code="en",  # Используем английскую модель как fallback
                    device=self.device,  # Используем определенное устройство
                    cache_dir=cache_dir  # Используем кэш для загрузки
                )
                logger.info(f"✅ Universal alignment model loaded on {self.device.upper()}")
                
            except Exception as e2:
                logger.warning(f"⚠️ Failed to load universal alignment model: {e2}")
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
        
        log("INFO", "🔍 Analyzing pauses in audio...")
        
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
            
            log("INFO", f"🔍 Detected pauses: {len(pauses)}")
            
            return pauses
            
        except Exception as e:
            log("WARNING", f"⚠️ Error analyzing pauses: {e}")
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
        
        log("INFO", f"🎤 Starting file transcription: {file_path.name}")
        
        # Переменные для очистки
        audio_file_path = None
        temp_audio_path = None
        
        try:
            update_progress(10, "Preparing audio...")
            
            # Конвертируем в аудио если необходимо
            if file_extension.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                log("INFO", "📹 Video file detected, but video conversion is not supported in this service.")
                log("INFO", "Please use the video_to_audio service first to convert video to audio.")
                raise RuntimeError("Video files are not supported. Please convert video to audio first using the video_to_audio service.")
            else:
                log("INFO", "🎵 Using original audio file")
                audio_file_path = file_path
            
            update_progress(35, "Analyzing pauses...")
            
            # Анализ пауз
            pauses = self._detect_pauses(audio_file_path, log_callback)
            
            update_progress(40, "Loading audio into Whisper...")
            
            # Загружаем аудио для Whisper
            audio = whisperx.load_audio(str(audio_file_path))
            
            update_progress(50, "Performing transcription...")
            
            # Основная транскрипция
            log("INFO", f"🎯 Performing transcription (model: {self.model_size}, device: {self.device})")
            
            result = self.model.transcribe(
                audio,
                batch_size=16 if self.device == "cuda" else 4
            )
            
            update_progress(75, "Aligning words...")
            
            # Выравнивание слов (если модель доступна)
            if self.align_model is not None:
                try:
                    log("INFO", "🎯 Aligning words with timestamps...")
                    
                    result = whisperx.align(
                        result["segments"],
                        self.align_model,
                        whisperx.utils.get_writer_output_format("json"),
                        audio,
                        self.device,  # Используем определенное устройство
                        return_char_alignments=False
                    )
                    
                    log("INFO", "✅ Word alignment completed successfully")
                    
                except Exception as e:
                    log("WARNING", f"⚠️ Alignment error: {e}")
                    # Создаем простую разбивку по словам на основе сегментов
                    log("INFO", "🔄 Creating simple word breakdown...")
                    result = self._create_simple_word_alignment(result)
            else:
                log("INFO", "🔄 Alignment model not available, creating simple word breakdown...")
                result = self._create_simple_word_alignment(result)
            
            update_progress(90, "Formatting result...")
            
            # Форматируем результат
            formatted_results = self._format_transcription_result(
                result,
                pauses,
                file_path.name,
                task_id
            )
            
            update_progress(100, "Transcription completed!")
            
            log("INFO", "✅ Transcription completed successfully")
            
            return formatted_results
            
        except Exception as e:
            log("ERROR", f"❌ Transcription error: {e}")
            raise RuntimeError(f"Transcription error: {e}")
            
        finally:
            # Сохраняем временный аудио файл (не удаляем)
            if temp_audio_path and temp_audio_path.exists():
                log("INFO", f"💾 Temporary audio file saved: {temp_audio_path}")
            
            # Очистка GPU памяти
            if self.device == "cuda":
                torch.cuda.empty_cache()
                gc.collect()
    
    async def transcribe_audio_file(
        self,
        audio_path: Path,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Транскрибция аудио файла с сохранением результатов
        
        Args:
            audio_path: Путь к аудио файлу
            task_id: ID задачи
            
        Returns:
            Результат транскрипции с информацией о сохраненных файлах
        """
        
        logger.info(f"🎤 Starting audio transcription: {audio_path.name}")
        
        try:
            # Получаем расширение файла
            file_extension = audio_path.suffix.lower()
            
            # Выполняем транскрипцию
            formatted_results = await self.transcribe_file(
                file_path=audio_path,
                file_extension=file_extension,
                task_id=task_id
            )
            
            # Сохраняем результаты в файлы
            txt_filename = f"{task_id}_transcription.txt"
            json_filename = f"{task_id}_transcription.json"
            
            txt_path = settings.OUTPUT_DIR / txt_filename
            json_path = settings.OUTPUT_DIR / json_filename
            
            # Сохраняем простой текст
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(formatted_results['simple_text'])
            
            # Сохраняем timeline результат в JSON
            json_data = {
                "timeline": formatted_results['timeline']
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Transcription files saved: {txt_filename}, {json_filename}")
            
            # Возвращаем результат с информацией о файлах
            return {
                "status": "success",
                "task_id": task_id,
                "transcription": formatted_results['simple_text'],
                "timeline": formatted_results['timeline'],
                "saved_files": {
                    "txt": txt_filename,
                    "json": json_filename
                },
                "model_used": self.model_size,
                "device_used": self.device,
                "language": self.language
            }
            
        except Exception as e:
            logger.error(f"❌ Error in transcribe_audio_file: {e}")
            raise RuntimeError(f"Transcription failed: {str(e)}")
    
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
    ) -> Dict[str, Any]:
        """
        Форматирование результата транскрипции в два отдельных файла
        
        Args:
            whisper_result: Результат от WhisperX
            pauses: Список пауз
            filename: Имя исходного файла
            task_id: ID задачи
            
        Returns:
            Словарь с простым текстом и timeline данными
        """
        
        segments = whisper_result.get("segments", [])
        
        # 1. Простой текст (только полный текст без заголовков)
        full_text = " ".join(
            segment.get('text', '').strip()
            for segment in segments
        ).strip()
        
        # 2. Timeline данные для JSON
        timeline = []
        
        # Добавляем слова с временными метками
        for segment in segments:
            words = segment.get('words', [])
            
            for word_info in words:
                timeline.append({
                    "type": "word",
                    "text": word_info.get('word', '').strip(),
                    "start": word_info.get('start', 0),
                    "end": word_info.get('end', 0)
                })
        
        # Добавляем паузы
        for pause in pauses:
            timeline.append({
                "type": "pause",
                "start": pause['start'],
                "end": pause['end'],
                "duration": pause['duration']
            })
        
        # Сортируем timeline по времени начала
        timeline.sort(key=lambda x: x['start'])
        
        return {
            'simple_text': full_text,
            'timeline': timeline
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
