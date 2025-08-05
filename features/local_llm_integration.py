"""
Local LLM Integration with Ollama
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

import httpx
# import ollama  # Temporarily commented out due to missing dependency
# from ollama import AsyncClient  # Temporarily commented out due to missing dependency

from utils.exceptions import LLMError, InitializationError


class LocalLLMManager:
    """
    Manage local LLM integration with Ollama
    """

    def __init__(self, ollama_endpoint="http://localhost:11434"):
        self.ollama_endpoint = ollama_endpoint
        # Temporarily handle missing ollama dependency
        try:
            from ollama import AsyncClient
            self.client = AsyncClient(host=ollama_endpoint)
            self.ollama_available = True
        except ImportError:
            self.client = None
            self.ollama_available = False

        self.available_models = {}
        self.model_capabilities = {
            "llama3.3": {"strength": "general", "context": 8192, "speed": "medium"},
            "mistral": {"strength": "reasoning", "context": 4096, "speed": "fast"},
            "codellama": {"strength": "code", "context": 16384, "speed": "slow"},
            "llama3.2": {"strength": "general", "context": 4096, "speed": "fast"},
            "qwen2.5": {"strength": "multilingual", "context": 8192, "speed": "medium"}
        }
        self.model_load_times = {}
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize and verify available models"""
        try:
            self.logger.info("🤖 Initializing Local LLM Manager...")

            # Check if ollama is available
            if not self.ollama_available:
                self.logger.warning("⚠️ Ollama package not available. Local LLM features disabled.")
                return

            # Check if Ollama is running
            await self._check_ollama_connection()

            # Discover available models
            self.available_models = await self.discover_models()

            if not self.available_models:
                self.logger.warning("⚠️ No models found. Please install models using 'ollama pull <model>'")
            else:
                self.logger.info(f"✅ Found {len(self.available_models)} available models")

            # Warm up default models
            await self.warm_up_models()

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize LLM Manager: {e}")
            raise InitializationError(f"LLM Manager initialization failed: {e}")

    async def _check_ollama_connection(self):
        """Check if Ollama service is running"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_endpoint}/api/tags", timeout=10.0)
                if response.status_code != 200:
                    raise LLMError(f"Ollama service not responding: {response.status_code}")
        except httpx.RequestError as e:
            raise LLMError(f"Cannot connect to Ollama at {self.ollama_endpoint}: {e}")

    async def discover_models(self) -> Dict[str, Any]:
        """Discover available models from Ollama"""
        try:
            models = await self.client.list()
            available = {}

            for model in models.get('models', []):
                model_name = model['name'].split(':')[0]  # Remove tag
                available[model_name] = {
                    'name': model['name'],
                    'size': model.get('size', 0),
                    'modified_at': model.get('modified_at'),
                    'capabilities': self.model_capabilities.get(model_name, {
                        'strength': 'unknown',
                        'context': 4096,
                        'speed': 'medium'
                    })
                }

            return available

        except Exception as e:
            self.logger.error(f"Failed to discover models: {e}")
            return {}

    async def warm_up_models(self):
        """Warm up commonly used models"""
        priority_models = ['llama3.3', 'mistral', 'llama3.2']

        for model_name in priority_models:
            if model_name in self.available_models:
                try:
                    await self.warm_up_model(model_name)
                except Exception as e:
                    self.logger.warning(f"Failed to warm up {model_name}: {e}")

    async def warm_up_model(self, model_name: str):
        """Warm up a specific model"""
        if model_name not in self.available_models:
            self.logger.warning(f"Model {model_name} not available")
            return

        try:
            start_time = time.time()
            self.logger.info(f"🔥 Warming up model: {model_name}")

            # Send a simple prompt to load the model
            await self.client.generate(
                model=model_name,
                prompt="Hello",
                options={'num_predict': 1}
            )

            load_time = time.time() - start_time
            self.model_load_times[model_name] = load_time
            self.logger.info(f"✅ Model {model_name} warmed up in {load_time:.2f}s")

        except Exception as e:
            self.logger.error(f"Failed to warm up {model_name}: {e}")
            raise LLMError(f"Model warm-up failed: {e}")

    async def select_optimal_model(self, task_type: str, content_size: int) -> str:
        """
        Automatically select best model for the task
        """
        if not self.available_models:
            raise LLMError("No models available")

        # Task-specific model selection
        if task_type == "code_analysis" and "codellama" in self.available_models:
            return "codellama"
        elif task_type == "extraction" and content_size > 4000:
            if "llama3.3" in self.available_models:
                return "llama3.3"
            elif "qwen2.5" in self.available_models:
                return "qwen2.5"
        elif task_type == "reasoning" and "mistral" in self.available_models:
            return "mistral"

        # Default fallback - prefer faster models for general tasks
        preferred_order = ["mistral", "llama3.2", "llama3.3", "qwen2.5", "codellama"]

        for model in preferred_order:
            if model in self.available_models:
                return model

        # Return any available model
        return list(self.available_models.keys())[0]

    async def process_content(
        self,
        content: str,
        task_type: str,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> str:
        """
        Process content through local LLM with intelligent chunking
        """
        if not model_name:
            model_name = await self.select_optimal_model(task_type, len(content))

        if model_name not in self.available_models:
            raise LLMError(f"Model {model_name} not available")

        model_context = self.model_capabilities.get(model_name, {}).get("context", 4096)

        # Handle large content with intelligent chunking
        if len(content) > model_context * 0.8:  # Leave some room for prompt
            return await self.process_chunked_content(content, model_name, task_type, temperature, max_tokens)

        return await self.single_pass_processing(content, model_name, task_type, temperature, max_tokens)

    async def single_pass_processing(
        self,
        content: str,
        model_name: str,
        task_type: str,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> str:
        """Process content in a single pass"""
        try:
            start_time = time.time()

            response = await self.client.generate(
                model=model_name,
                prompt=content,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                    'top_p': 0.9,
                    'top_k': 40
                }
            )

            processing_time = time.time() - start_time
            self.logger.debug(f"LLM processing completed in {processing_time:.2f}s")

            return response['response']

        except Exception as e:
            self.logger.error(f"LLM processing failed: {e}")
            raise LLMError(f"Content processing failed: {e}")

    async def process_chunked_content(
        self,
        content: str,
        model_name: str,
        task_type: str,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> str:
        """Process large content by chunking"""
        model_context = self.model_capabilities.get(model_name, {}).get("context", 4096)
        chunk_size = int(model_context * 0.6)  # Conservative chunk size

        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        results = []

        self.logger.info(f"Processing {len(chunks)} chunks with {model_name}")

        for i, chunk in enumerate(chunks):
            try:
                chunk_prompt = f"""
                This is part {i+1} of {len(chunks)} of a larger content.
                Task: {task_type}

                Content chunk:
                {chunk}

                Please process this chunk and provide relevant information.
                """

                result = await self.single_pass_processing(
                    chunk_prompt, model_name, task_type, temperature, max_tokens
                )
                results.append(result)

                # Small delay between chunks to avoid overwhelming the model
                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.warning(f"Failed to process chunk {i+1}: {e}")
                results.append(f"[Chunk {i+1} processing failed]")

        # Combine results
        combined_result = "\n\n".join(results)

        # If results are still too long, summarize
        if len(combined_result) > model_context:
            summary_prompt = f"""
            Please summarize the following combined results from multiple content chunks:

            {combined_result[:model_context//2]}

            Provide a concise summary that captures the key information.
            """

            try:
                combined_result = await self.single_pass_processing(
                    summary_prompt, model_name, "summarization", temperature, max_tokens
                )
            except Exception as e:
                self.logger.warning(f"Failed to summarize results: {e}")

        return combined_result

    async def analyze_content(self, content: str, content_type: str) -> Dict[str, Any]:
        """Analyze content and provide insights"""
        analysis_prompt = f"""
        Analyze the following {content_type} content and provide insights:

        Content:
        {content[:2000]}  # Limit content length

        Please provide:
        1. Content summary
        2. Key topics or themes
        3. Sentiment (if applicable)
        4. Important entities or data points
        5. Content quality assessment

        Return the analysis in JSON format.
        """

        try:
            model_name = await self.select_optimal_model("analysis", len(analysis_prompt))
            result = await self.process_content(analysis_prompt, "analysis", model_name)

            # Try to parse as JSON
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {
                    "summary": result,
                    "content_type": content_type,
                    "analysis_method": "text_response"
                }

        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return {
                "error": str(e),
                "content_type": content_type
            }

    async def get_status(self) -> Dict[str, Any]:
        """Get LLM manager status"""
        return {
            "ollama_endpoint": self.ollama_endpoint,
            "available_models": list(self.available_models.keys()),
            "model_count": len(self.available_models),
            "model_load_times": self.model_load_times,
            "capabilities": self.model_capabilities
        }

    async def get_available_models(self) -> Dict[str, Any]:
        """Get detailed information about available models"""
        return self.available_models

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("🧹 Cleaning up LLM Manager...")
        # Close any open connections if needed
        self.logger.info("✅ LLM Manager cleanup completed")