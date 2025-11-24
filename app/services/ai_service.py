"""
AI 模型服务 - 多平台适配层
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional
import openai
from dashscope import Generation
import dashscope
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.utils.logger import logger
from app.utils.exceptions import AIServiceException


class BaseModelProvider(ABC):
    """模型提供商基类"""
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: list, 
        model: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """同步聊天完成"""
        pass
    
    @abstractmethod
    async def chat_completion_stream(
        self, 
        messages: list, 
        model: str, 
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式聊天完成"""
        pass


class OpenAIProvider(BaseModelProvider):
    """OpenAI 模型提供商"""
    
    def __init__(self, api_key: str, api_base: Optional[str] = None):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=api_base or "https://api.openai.com/v1"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError)),
        reraise=True
    )
    async def chat_completion(self, messages: list, model: str, **kwargs):
        try:
            logger.info(f"调用 OpenAI API: model={model}")
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except (openai.APITimeoutError, openai.APIConnectionError) as e:
            logger.warning(f"OpenAI API 超时/连接错误，将重试: {e}")
            raise  # 让 tenacity 处理重试
        except openai.APIError as e:
            logger.error(f"OpenAI API 错误: {e}")
            raise AIServiceException(f"OpenAI API 错误: {str(e)}")
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise AIServiceException(f"OpenAI API 调用失败: {str(e)}")
    
    async def chat_completion_stream(self, messages: list, model: str, **kwargs):
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "done": False
                    }
            
            # 最后一个块标记完成
            yield {"content": "", "done": True}
            
        except Exception as e:
            logger.error(f"OpenAI 流式 API 调用失败: {e}")
            raise AIServiceException(f"OpenAI 流式 API 调用失败: {str(e)}")


class QwenProvider(BaseModelProvider):
    """通义千问模型提供商"""
    
    def __init__(self, api_key: str):
        dashscope.api_key = api_key
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def chat_completion(self, messages: list, model: str, **kwargs):
        try:
            # DashScope 是同步API,需要在线程池中运行
            import asyncio
            loop = asyncio.get_event_loop()
            logger.info(f"调用通义千问 API: model={model}")
            response = await loop.run_in_executor(
                None,
                lambda: Generation.call(
                    model=model,
                    messages=messages,
                    result_format='message',
                    **kwargs
                )
            )
            
            if response.status_code != 200:
                logger.error(f"通义千问 API 错误: {response.message}")
                raise AIServiceException(f"通义千问 API 错误: {response.message}")
            
            return {
                "content": response.output.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except AIServiceException:
            raise
        except Exception as e:
            logger.error(f"通义千问 API 调用失败: {e}")
            raise AIServiceException(f"通义千问 API 调用失败: {str(e)}")
    
    async def chat_completion_stream(self, messages: list, model: str, **kwargs):
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 获取生成器
            responses = await loop.run_in_executor(
                None,
                lambda: Generation.call(
                    model=model,
                    messages=messages,
                    result_format='message',
                    stream=True,
                    **kwargs
                )
            )
            
            for response in responses:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    if content:
                        yield {
                            "content": content,
                            "done": False
                        }
                else:
                    raise AIServiceException(f"通义千问流式 API 错误: {response.message}")
            
            yield {"content": "", "done": True}
            
        except Exception as e:
            logger.error(f"通义千问流式 API 调用失败: {e}")
            raise AIServiceException(f"通义千问流式 API 调用失败: {str(e)}")


class DeepSeekProvider(BaseModelProvider):
    """DeepSeek 模型提供商(OpenAI 兼容)"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.deepseek.com/v1"):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=api_base
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError)),
        reraise=True
    )
    async def chat_completion(self, messages: list, model: str, **kwargs):
        try:
            logger.info(f"调用 DeepSeek API: model={model}")
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except (openai.APITimeoutError, openai.APIConnectionError) as e:
            logger.warning(f"DeepSeek API 超时/连接错误，将重试: {e}")
            raise
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            raise AIServiceException(f"DeepSeek API 调用失败: {str(e)}")
    
    async def chat_completion_stream(self, messages: list, model: str, **kwargs):
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "done": False
                    }
            
            yield {"content": "", "done": True}
            
        except Exception as e:
            logger.error(f"DeepSeek 流式 API 调用失败: {e}")
            raise AIServiceException(f"DeepSeek 流式 API 调用失败: {str(e)}")


class SiliconFlowProvider(BaseModelProvider):
    """硅基流动模型提供商(OpenAI 兼容)"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.siliconflow.cn/v1"):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=api_base
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError)),
        reraise=True
    )
    async def chat_completion(self, messages: list, model: str, **kwargs):
        try:
            logger.info(f"调用硅基流动 API: model={model}")
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except (openai.APITimeoutError, openai.APIConnectionError) as e:
            logger.warning(f"硅基流动 API 超时/连接错误，将重试: {e}")
            raise
        except Exception as e:
            logger.error(f"硅基流动 API 调用失败: {e}")
            raise AIServiceException(f"硅基流动 API 调用失败: {str(e)}")
    
    async def chat_completion_stream(self, messages: list, model: str, **kwargs):
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "done": False
                    }
            
            yield {"content": "", "done": True}
            
        except Exception as e:
            logger.error(f"硅基流动流式 API 调用失败: {e}")
            raise AIServiceException(f"硅基流动流式 API 调用失败: {str(e)}")


class AIModelService:
    """AI 模型服务统一入口"""
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "qwen": QwenProvider,
        "deepseek": DeepSeekProvider,
        "siliconflow": SiliconFlowProvider,
    }
    
    @classmethod
    def get_provider(
        cls, 
        provider: str, 
        api_key: str, 
        api_base: Optional[str] = None
    ) -> BaseModelProvider:
        """获取模型提供商实例"""
        provider_class = cls.PROVIDERS.get(provider)
        if not provider_class:
            raise ValueError(f"不支持的模型提供商: {provider}")
        
        if provider == "openai" and api_base:
            return provider_class(api_key, api_base)
        elif provider in ["deepseek", "siliconflow"] and api_base:
            return provider_class(api_key, api_base)
        elif provider == "openai":
            return provider_class(api_key)
        elif provider == "qwen":
            return provider_class(api_key)
        elif provider == "deepseek":
            return provider_class(api_key)
        elif provider == "siliconflow":
            return provider_class(api_key)
        
        return provider_class(api_key)
    
    @classmethod
    async def chat(
        cls, 
        provider: str,
        api_key: str,
        model: str,
        messages: list,
        stream: bool = False,
        api_base: Optional[str] = None,
        **kwargs
    ):
        """
        统一的聊天接口
        
        Args:
            provider: 模型提供商
            api_key: API密钥
            model: 模型名称
            messages: 消息列表
            stream: 是否流式输出
            api_base: API基础URL(可选)
            **kwargs: 其他模型参数
        
        Returns:
            非流式: Dict[str, Any]
            流式: AsyncIterator[Dict[str, Any]]
        """
        provider_instance = cls.get_provider(provider, api_key, api_base)
        
        if stream:
            return provider_instance.chat_completion_stream(messages, model, **kwargs)
        else:
            return await provider_instance.chat_completion(messages, model, **kwargs)

