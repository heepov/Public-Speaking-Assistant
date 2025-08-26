"""
Сервис для обработки текста с помощью Ollama
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime
import requests

import torch
import ollama
from openai import OpenAI

from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)


class OllamaProcessingService:
    """Сервис для обработки текста с помощью Ollama"""
    
    def __init__(self):
        self.ollama_client = None
        self.openai_client = None
        self.is_initialized = False
        self.available_models = []
        self.default_model = "llama2"
        self.ollama_host = os.environ.get("OLLAMA_HOST", "localhost:11434")
        
    async def initialize(self):
        """Инициализация Ollama клиента"""
        try:
            logger.info("🚀 Инициализация Ollama сервиса...")
            
            # Подробная проверка GPU доступности
            logger.info("=" * 60)
            logger.info("🔍 ПРОВЕРКА GPU ПОДДЕРЖКИ")
            logger.info("=" * 60)
            
            # PyTorch CUDA
            logger.info(f"🔍 PyTorch CUDA доступен: {torch.cuda.is_available()}")
            logger.info(f"🔍 PyTorch CUDA устройств: {torch.cuda.device_count()}")
            
            if torch.cuda.is_available():
                logger.info(f"🔍 PyTorch CUDA устройство: {torch.cuda.get_device_name(0)}")
                logger.info(f"🔍 PyTorch CUDA память: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
                logger.info(f"🔍 PyTorch CUDA версия: {torch.version.cuda}")
            
            # Переменные окружения
            logger.info(f"🔍 OLLAMA_HOST: {self.ollama_host}")
            logger.info(f"🔍 CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'НЕ УСТАНОВЛЕНА')}")
            
            logger.info("=" * 60)
            
            # Проверка доступности Ollama
            logger.info("🔍 Проверка доступности Ollama...")
            try:
                response = requests.get(f"http://{self.ollama_host}/api/tags", timeout=10)
                if response.status_code == 200:
                    logger.info("✅ Ollama доступен")
                    models_data = response.json()
                    self.available_models = [model['name'] for model in models_data.get('models', [])]
                    logger.info(f"📦 Доступные модели: {self.available_models}")
                else:
                    logger.warning(f"⚠️  Ollama недоступен, статус: {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️  Не удалось подключиться к Ollama: {e}")
            
            # Инициализация Ollama клиента
            logger.info("🔧 Инициализация Ollama клиента...")
            self.ollama_client = ollama.Client(host=f"http://{self.ollama_host}")
            
            # Проверка доступности OpenAI (опционально)
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if openai_api_key:
                logger.info("🔧 Инициализация OpenAI клиента...")
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("✅ OpenAI клиент инициализирован")
            
            # Установка модели по умолчанию если не установлена
            if not self.available_models:
                logger.info("📥 Установка модели по умолчанию...")
                try:
                    await self._install_default_model()
                except Exception as e:
                    logger.warning(f"⚠️  Не удалось установить модель по умолчанию: {e}")
            
            self.is_initialized = True
            logger.info("✅ Ollama сервис успешно инициализирован")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации Ollama сервиса: {e}")
            raise
    
    async def _install_default_model(self):
        """Установка модели по умолчанию"""
        try:
            logger.info(f"📥 Установка модели {self.default_model}...")
            
            # Используем subprocess для асинхронной установки
            import subprocess
            import asyncio
            
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", self.default_model,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ Модель {self.default_model} успешно установлена")
                self.available_models.append(self.default_model)
            else:
                logger.error(f"❌ Ошибка установки модели: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при установке модели: {e}")
            raise
    
    async def process_text(
        self,
        prompt: str,
        input_data: Optional[Dict[str, Any]] = None,
        instructions_file: Optional[str] = None,
        task_id: str = "",
        model_name: str = None,
        use_openai: bool = False,
        system_prompt: Optional[str] = None,
        model_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Обработка текста с помощью Ollama или OpenAI
        
        Args:
            prompt: Промпт для обработки (обязательный)
            input_data: Входные данные (текст, JSON и т.д.) - опционально
            instructions_file: Путь к файлу с инструкциями (опционально)
            task_id: ID задачи
            model_name: Название модели Ollama
            use_openai: Использовать OpenAI вместо Ollama
            system_prompt: Системный промпт (опционально, если не указан - создается автоматически)
            model_params: Параметры модели (temperature, top_p, num_predict, repeat_penalty, presence_penalty и др.)
            
        Returns:
            Результат обработки
        """
        
        if not self.is_initialized:
            raise RuntimeError("Сервис не инициализирован")
        
        try:
            logger.info("=" * 60)
            logger.info(f"🔄 ОБРАБОТКА ТЕКСТА - task_id: {task_id}")
            logger.info("=" * 60)
            
            # Загрузка инструкций если указан файл
            instructions = ""
            if instructions_file and Path(instructions_file).exists():
                with open(instructions_file, 'r', encoding='utf-8') as f:
                    instructions = f.read()
                logger.info(f"📖 Загружены инструкции из файла: {instructions_file}")
                logger.info(f"📖 Размер инструкций: {len(instructions)} символов")
            else:
                logger.info("📖 Инструкции не предоставлены, используются стандартные")
            
            # Подготовка входных данных
            input_text = ""
            if input_data is not None:
                input_text = self._prepare_input(input_data)
                logger.info(f"📄 Размер входного текста: {len(input_text)} символов")
            else:
                logger.info("📄 Входные данные не предоставлены, используется только промпт")
            
            # Формирование промпта для модели
            if system_prompt is None:
                system_prompt = self._create_default_system_prompt(instructions)
            user_prompt = self._create_user_prompt(input_text, prompt)
            
            logger.info(f"💬 Размер системного промпта: {len(system_prompt)} символов")
            logger.info(f"💬 Размер пользовательского промпта: {len(user_prompt)} символов")
            logger.info(f"💬 Общий размер промпта: {len(system_prompt) + len(user_prompt)} символов")
            
            # Выбор модели
            if use_openai and self.openai_client:
                logger.info("🤖 Использование OpenAI для обработки...")
                result = await self._process_with_openai(system_prompt, user_prompt, task_id, model_params)
                model_used = "openai-gpt-3.5-turbo"
            else:
                # Используем Ollama
                model_to_use = model_name or self.default_model
                logger.info(f"🤖 Использование Ollama модели: {model_to_use}")
                result = await self._process_with_ollama(system_prompt, user_prompt, model_to_use, task_id, model_params)
                model_used = model_to_use
            
            # Сохранение результата
            output_path = self._save_result(result, task_id)
            
            logger.info(f"💾 Результат сохранен: {output_path}")
            logger.info("=" * 60)
            
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "output_file": str(output_path),
                "timestamp": datetime.now().isoformat(),
                "model": model_used,
                "service": "openai" if use_openai else "ollama"
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке текста: {e}")
            raise
    
    async def _process_with_ollama(self, system_prompt: str, user_prompt: str, model_name: str, task_id: str, model_params: Optional[Dict[str, Any]] = None) -> str:
        """Обработка с помощью Ollama"""
        try:
            logger.info("🚀 Начинаем инференс с Ollama...")
            start_time = datetime.now()
            
            # Проверяем доступность модели
            logger.info(f"🔍 Проверяем доступность модели: {model_name}")
            try:
                models_response = requests.get(f"http://{self.ollama_host}/api/tags", timeout=10)
                if models_response.status_code == 200:
                    available_models = [model['name'] for model in models_response.json().get('models', [])]
                    if model_name not in available_models:
                        logger.warning(f"⚠️  Модель {model_name} не найдена. Доступные: {available_models}")
                        # Пытаемся использовать первую доступную модель
                        if available_models:
                            model_name = available_models[0]
                            logger.info(f"🔄 Используем модель: {model_name}")
                        else:
                            raise Exception("Нет доступных моделей Ollama")
            except Exception as e:
                logger.warning(f"⚠️  Не удалось проверить доступные модели: {e}")
            
            # Формируем полный промпт
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Подготавливаем параметры модели
            default_options = {
                "temperature": 0.95,
                "top_p": 0.9,
                "num_predict": 800,
                "repeat_penalty": 1.2,
                "presence_penalty": 0.8
            }
            
            if model_params:
                default_options.update(model_params)
                logger.info(f"🔧 Используются пользовательские параметры модели: {model_params}")
            else:
                logger.info(f"🔧 Используются параметры по умолчанию: {default_options}")
            
            # Выполняем запрос к Ollama
            response = self.ollama_client.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options=default_options
            )
            
            end_time = datetime.now()
            inference_time = (end_time - start_time).total_seconds()
            
            result = response['message']['content'].strip()
            
            logger.info(f"✅ Инференс завершен за {inference_time:.2f} секунд")
            logger.info(f"📊 Размер результата: {len(result)} символов")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке с Ollama: {e}")
            logger.error(f"🔍 Детали ошибки: {type(e).__name__}")
            raise
    
    async def _process_with_openai(self, system_prompt: str, user_prompt: str, task_id: str, model_params: Optional[Dict[str, Any]] = None) -> str:
        """Обработка с помощью OpenAI"""
        try:
            logger.info("🚀 Начинаем инференс с OpenAI...")
            start_time = datetime.now()
            
            # Подготавливаем параметры модели
            default_params = {
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            if model_params:
                # Фильтруем параметры, которые поддерживает OpenAI
                openai_supported_params = {
                    "max_tokens", "temperature", "top_p", "frequency_penalty", 
                    "presence_penalty", "stop", "n", "stream"
                }
                filtered_params = {k: v for k, v in model_params.items() if k in openai_supported_params}
                default_params.update(filtered_params)
                logger.info(f"🔧 Используются пользовательские параметры OpenAI: {filtered_params}")
            else:
                logger.info(f"🔧 Используются параметры OpenAI по умолчанию: {default_params}")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                **default_params
            )
            
            end_time = datetime.now()
            inference_time = (end_time - start_time).total_seconds()
            
            result = response.choices[0].message.content.strip()
            
            logger.info(f"✅ Инференс завершен за {inference_time:.2f} секунд")
            logger.info(f"📊 Размер результата: {len(result)} символов")
            logger.info(f"📊 Использовано токенов: {response.usage.total_tokens}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке с OpenAI: {e}")
            raise
    
    def _prepare_input(self, input_data: Dict[str, Any]) -> str:
        """Подготовка входных данных"""
        if isinstance(input_data, dict):
            return json.dumps(input_data, ensure_ascii=False, indent=2)
        elif isinstance(input_data, str):
            return input_data
        else:
            return str(input_data)
    
    def _create_default_system_prompt(self, instructions: str) -> str:
        """Создание системного промпта по умолчанию"""
        base_prompt = """Ты - помощник для анализа и обработки текстовых данных. 
Твоя задача - внимательно анализировать предоставленные данные и выполнять указанные инструкции."""
        
        if instructions:
            return f"{base_prompt}\n\nИнструкции:\n{instructions}"
        
        return base_prompt
    
    def _create_user_prompt(self, input_text: str, prompt: str) -> str:
        """Создание пользовательского промпта"""
        if input_text:
            return f"Данные для обработки:\n{input_text}\n\nЗадача: {prompt}"
        else:
            return f"Задача: {prompt}"
    
    def _save_result(self, result: str, task_id: str) -> Path:
        """Сохранение результата в файл"""
        output_dir = Path(settings.OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"ollama_result_{task_id}_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        return output_file
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели"""
        return {
            "service": "ollama",
            "ollama_host": self.ollama_host,
            "available_models": self.available_models,
            "default_model": self.default_model,
            "is_initialized": self.is_initialized,
            "openai_available": self.openai_client is not None,
            "gpu_available": torch.cuda.is_available()
        }
    
    async def list_models(self) -> List[str]:
        """Получение списка доступных моделей"""
        try:
            response = requests.get(f"http://{self.ollama_host}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                return [model['name'] for model in models_data.get('models', [])]
            else:
                return []
        except Exception as e:
            logger.error(f"❌ Ошибка при получении списка моделей: {e}")
            return []
    
    async def install_model(self, model_name: str) -> bool:
        """Установка модели"""
        try:
            logger.info(f"📥 Установка модели {model_name}...")
            
            import subprocess
            import asyncio
            
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ Модель {model_name} успешно установлена")
                # Обновляем список доступных моделей
                self.available_models = await self.list_models()
                return True
            else:
                logger.error(f"❌ Ошибка установки модели: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при установке модели: {e}")
            return False
