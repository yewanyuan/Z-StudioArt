"""Z-Image-Turbo AI 模型客户端 (ModelScope API)

实现与 ModelScope Z-Image-Turbo 模型的交互，支持图像生成和批量生成。

Requirements:
- 2.1: 单张海报生成在 5 秒内返回
- 2.2: 预览模式生成 4 张变体图
- 5.1, 5.2, 5.3: 支持 1:1, 9:16, 16:9 尺寸比例
"""

import asyncio
import time
from typing import Literal, Optional

import httpx

from app.core.config import settings
from app.models.schemas import GeneratedImageData, GenerationOptions


DEFAULT_BASE_SIZE = 1024


class AspectRatioCalculator:
    """图像尺寸计算器"""
    
    ASPECT_RATIOS: dict[str, tuple[int, int]] = {
        "1:1": (1, 1),
        "9:16": (9, 16),
        "16:9": (16, 9),
    }
    
    @classmethod
    def calculate_dimensions(
        cls,
        aspect_ratio: str,
        base_size: int = DEFAULT_BASE_SIZE,
        custom_width: Optional[int] = None,
        custom_height: Optional[int] = None,
    ) -> tuple[int, int]:
        if aspect_ratio == "custom":
            if not custom_width or not custom_height:
                raise ValueError("custom_width and custom_height must be provided when aspect_ratio is 'custom'")
            return (custom_width, custom_height)

        if aspect_ratio not in cls.ASPECT_RATIOS:
            raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
        
        ratio_w, ratio_h = cls.ASPECT_RATIOS[aspect_ratio]
        
        if ratio_w >= ratio_h:
            width = base_size
            height = int(base_size * ratio_h / ratio_w)
        else:
            height = base_size
            width = int(base_size * ratio_w / ratio_h)
        
        return (width, height)
    
    @classmethod
    def validate_dimensions(
        cls,
        width: int,
        height: int,
        aspect_ratio: Literal["1:1", "9:16", "16:9"],
        tolerance: int = 1
    ) -> bool:
        ratio_w, ratio_h = cls.ASPECT_RATIOS[aspect_ratio]
        expected_ratio = ratio_w / ratio_h
        min_ratio = max(width - tolerance, 1) / (height + tolerance)
        max_ratio = (width + tolerance) / max(height - tolerance, 1)
        return min_ratio <= expected_ratio <= max_ratio


class ZImageTurboClient:
    """Z-Image-Turbo AI 模型客户端 (ModelScope API)
    
    使用 ModelScope 异步 API 进行图像生成。
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        poll_interval: float = 1.0
    ):
        self.api_key = api_key or settings.modelscope_api_key
        self.base_url = (base_url or settings.modelscope_base_url).rstrip("/")
        self.timeout_ms = timeout_ms or settings.zimage_timeout
        self.poll_interval = poll_interval
        self._model_version = "Tongyi-MAI/Z-Image-Turbo"
    
    def _get_headers(self, async_mode: bool = False) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if async_mode:
            headers["X-ModelScope-Async-Mode"] = "true"
        return headers
    
    def _get_task_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-ModelScope-Task-Type": "image_generation",
        }
    
    async def _submit_task(
        self,
        prompt: str,
        options: GenerationOptions,
        client: httpx.AsyncClient
    ) -> str:
        """提交生成任务，返回 task_id"""
        payload = {
            "model": self._model_version,
            "prompt": prompt,
        }
        
        # 添加可选参数
        if options.seed is not None:
            payload["seed"] = options.seed
        if options.width and options.height:
            payload["size"] = f"{options.width}x{options.height}"
        
        response = await client.post(
            f"{self.base_url}/v1/images/generations",
            headers=self._get_headers(async_mode=True),
            json=payload
        )
        response.raise_for_status()
        return response.json()["task_id"]
    
    async def _poll_task(
        self,
        task_id: str,
        client: httpx.AsyncClient,
        start_time: float
    ) -> bytes:
        """轮询任务状态，返回图像数据"""
        timeout_seconds = self.timeout_ms / 1000
        
        while True:
            elapsed = time.perf_counter() - start_time
            if elapsed > timeout_seconds:
                raise TimeoutError(f"Image generation timed out after {self.timeout_ms}ms")
            
            response = await client.get(
                f"{self.base_url}/v1/tasks/{task_id}",
                headers=self._get_task_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            if data["task_status"] == "SUCCEED":
                image_url = data["output_images"][0]
                image_response = await client.get(image_url)
                image_response.raise_for_status()
                return image_response.content
            elif data["task_status"] == "FAILED":
                raise RuntimeError(f"Image generation failed: {data.get('message', 'Unknown error')}")
            
            await asyncio.sleep(self.poll_interval)
    
    async def generate_image(
        self,
        prompt: str,
        options: GenerationOptions
    ) -> GeneratedImageData:
        """生成单张图像"""
        start_time = time.perf_counter()
        
        timeout = httpx.Timeout(self.timeout_ms / 1000 + 10, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            task_id = await self._submit_task(prompt, options, client)
            image_buffer = await self._poll_task(task_id, client, start_time)
        
        generation_time_ms = int((time.perf_counter() - start_time) * 1000)
        
        return GeneratedImageData(
            image_buffer=image_buffer,
            generation_time_ms=generation_time_ms,
            model_version=self._model_version
        )
    
    async def generate_batch(
        self,
        prompt: str,
        count: int,
        options: GenerationOptions
    ) -> list[GeneratedImageData]:
        """批量生成图像（串行执行，带延迟避免 API 限流）"""
        if count <= 0:
            return []
        
        base_seed = options.seed or int(time.time() * 1000) % (2**32)
        results = []
        
        for i in range(count):
            variant_options = GenerationOptions(
                width=options.width,
                height=options.height,
                seed=base_seed + i,
                guidance_scale=options.guidance_scale
            )
            result = await self.generate_image(prompt, variant_options)
            results.append(result)
            
            # 添加延迟避免 API 限流
            if i < count - 1:
                await asyncio.sleep(2.0)
        
        return results
    
    async def image_to_image(
        self,
        source_image: bytes,
        prompt: str,
        options: GenerationOptions
    ) -> GeneratedImageData:
        """图生图（场景融合）- 暂不支持，返回文生图结果"""
        # ModelScope Z-Image-Turbo 目前主要支持文生图
        # 场景融合功能可以通过 prompt 描述实现
        return await self.generate_image(prompt, options)



def calculate_image_dimensions(
    aspect_ratio: str,
    base_size: int = DEFAULT_BASE_SIZE,
    custom_width: Optional[int] = None,
    custom_height: Optional[int] = None,
) -> tuple[int, int]:
    """便捷函数：计算图像尺寸"""
    return AspectRatioCalculator.calculate_dimensions(
        aspect_ratio, base_size, custom_width, custom_height
    )


def validate_image_dimensions(
    width: int,
    height: int,
    aspect_ratio: Literal["1:1", "9:16", "16:9"],
    tolerance: int = 1
) -> bool:
    """便捷函数：验证图像尺寸"""
    return AspectRatioCalculator.validate_dimensions(
        width, height, aspect_ratio, tolerance
    )
