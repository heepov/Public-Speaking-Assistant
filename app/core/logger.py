"""
Система логирования для приложения
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Форматтер с цветным выводом для консоли"""
    
    # Цветовые коды ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Голубой
        'INFO': '\033[32m',       # Зеленый
        'WARNING': '\033[33m',    # Желтый
        'ERROR': '\033[31m',      # Красный
        'CRITICAL': '\033[35m',   # Фиолетовый
        'RESET': '\033[0m'        # Сброс цвета
    }
    
    # Эмодзи для разных уровней
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    def format(self, record):
        # Добавляем цвет и эмодзи к уровню логирования
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.COLORS['RESET'])
        emoji = self.EMOJIS.get(levelname, '')
        
        # Форматируем время
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Собираем сообщение
        colored_level = f"{color}{emoji} {levelname:<8}{self.COLORS['RESET']}"
        module_name = f"{record.name:<20}"
        
        return f"[{timestamp}] {colored_level} {module_name} | {record.getMessage()}"


class TranscriptionLogHandler(logging.Handler):
    """Кастомный обработчик логов для сохранения в память"""
    
    def __init__(self):
        super().__init__()
        self.logs = []
        self.max_logs = 1000  # Максимальное количество логов в памяти
    
    def emit(self, record):
        try:
            # Форматируем лог
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).strftime('%H:%M:%S'),
                'level': record.levelname,
                'module': record.name,
                'message': record.getMessage()
            }
            
            # Добавляем в список
            self.logs.append(log_entry)
            
            # Ограничиваем количество логов
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
                
        except Exception:
            self.handleError(record)
    
    def get_logs(self, limit: Optional[int] = None):
        """Получить последние логи"""
        if limit:
            return self.logs[-limit:]
        return self.logs.copy()
    
    def clear_logs(self):
        """Очистить логи"""
        self.logs.clear()


# Глобальный обработчик логов
transcription_log_handler = TranscriptionLogHandler()


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Настройка логгера с цветным выводом и файловым логированием
    
    Args:
        name: Имя логгера (обычно __name__)
        level: Уровень логирования
        
    Returns:
        Настроенный логгер
    """
    
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Проверяем, не настроен ли уже логгер
    if logger.handlers:
        return logger
    
    # Создаем директорию для логов с обработкой ошибок
    try:
        settings.LOGS_DIR.mkdir(exist_ok=True)
    except Exception as e:
        # Если не удается создать директорию, используем текущую
        settings.LOGS_DIR = Path(".")
        print(f"⚠️ Не удалось создать директорию logs: {e}, используем текущую директорию")
    
    # === КОНСОЛЬНЫЙ ВЫВОД ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    # === ФАЙЛОВОЕ ЛОГИРОВАНИЕ ===
    # В Docker среде не создаем файлы логов
    if not settings.DOCKER_ENV:
        # Общий лог файл
        file_handler = logging.FileHandler(
            settings.LOGS_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # JSON форматтер для файлов
        json_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)
        
        # === ОБРАБОТЧИК ОШИБОК ===
        error_handler = logging.FileHandler(
            settings.LOGS_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_formatter)
        logger.addHandler(error_handler)
    
    # === КАСТОМНЫЙ ОБРАБОТЧИК ДЛЯ ВЕБ-ИНТЕРФЕЙСА ===
    transcription_log_handler.setLevel(logging.INFO)
    logger.addHandler(transcription_log_handler)
    
    return logger


def get_recent_logs(limit: int = 100) -> list:
    """
    Получить последние логи для отображения в веб-интерфейсе
    
    Args:
        limit: Количество последних логов
        
    Returns:
        Список логов
    """
    return transcription_log_handler.get_logs(limit)


def clear_logs():
    """Очистить логи в памяти"""
    transcription_log_handler.clear_logs()


class ProgressLogger:
    """Класс для логирования прогресса длительных операций"""
    
    def __init__(self, name: str, total_steps: int = 100):
        self.logger = setup_logger(f"progress.{name}")
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()
    
    def update(self, step: int, message: str = ""):
        """
        Обновить прогресс
        
        Args:
            step: Текущий шаг (0-100)
            message: Дополнительное сообщение
        """
        self.current_step = step
        
        # Вычисляем процент
        percentage = min(100, max(0, step))
        
        # Вычисляем время выполнения
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]  # Убираем микросекунды
        
        # Создаем прогресс-бар
        bar_length = 20
        filled_length = int(bar_length * percentage // 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Логируем прогресс
        progress_msg = f"[{bar}] {percentage:3d}% | {elapsed_str}"
        if message:
            progress_msg += f" | {message}"
        
        self.logger.info(progress_msg)
    
    def complete(self, final_message: str = "Завершено"):
        """
        Завершить операцию
        
        Args:
            final_message: Финальное сообщение
        """
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        self.logger.info(f"✅ {final_message} | Время выполнения: {elapsed_str}")
    
    def error(self, error_message: str):
        """
        Сообщить об ошибке
        
        Args:
            error_message: Сообщение об ошибке
        """
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        self.logger.error(f"❌ {error_message} | Время до ошибки: {elapsed_str}")
