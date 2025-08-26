"""
Модуль для обработки текста с помощью Ollama
"""

from .service import OllamaProcessingService
from .microservice import app

__all__ = ["OllamaProcessingService", "app"]
