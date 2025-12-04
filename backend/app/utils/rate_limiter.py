"""Rate Limiter Service for PopGraph.

This module implements rate limiting functionality based on user membership tier.
Supports both Redis and in-memory storage (fallback when Redis is unavailable).

Requirements: 7.2 - WHEN a free-tier user exceeds 5 daily generations 
THEN the PopGraph System SHALL block further generation requests until the next day
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Protocol, Union

from app.core.config import settings
from app.models.schemas import MembershipTier, RateLimitResult, RATE_LIMIT_CONFIG


class StorageProtocol(Protocol):
    """存储后端协议，定义 Redis 和内存存储的通用接口"""
    
    async def get(self, key: str) -> Optional[str]: ...
    async def incr(self, key: str) -> int: ...
    async def expire(self, key: str, seconds: int) -> None: ...
    async def delete(self, key: str) -> None: ...


class InMemoryStorage:
    """内存存储（Redis 不可用时的降级方案）
    
    提供与 Redis 兼容的异步接口，用于开发环境或 Redis 不可用时的降级。
    
    特性：
    - 自动清理过期数据
    - 线程安全（单进程内）
    - 异步接口兼容
    """
    
    def __init__(self):
        self._data: dict[str, int] = {}
        self._expiry: dict[str, datetime] = {}
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        self._cleanup_expired()
        value = self._data.get(key)
        return str(value) if value is not None else None
    
    async def incr(self, key: str) -> int:
        """原子递增"""
        self._cleanup_expired()
        self._data[key] = self._data.get(key, 0) + 1
        return self._data[key]
    
    async def expire(self, key: str, seconds: int) -> None:
        """设置过期时间"""
        self._expiry[key] = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    
    async def delete(self, key: str) -> None:
        """删除键"""
        self._data.pop(key, None)
        self._expiry.pop(key, None)
    
    def _cleanup_expired(self) -> None:
        """清理过期数据"""
        now = datetime.now(timezone.utc)
        expired = [k for k, exp in self._expiry.items() if exp <= now]
        for k in expired:
            self._data.pop(k, None)
            self._expiry.pop(k, None)


class RateLimiter:
    """基于会员等级的限流服务
    
    支持 Redis 和内存存储两种模式，Redis 不可用时自动降级到内存存储。
    
    Attributes:
        _storage: 内存存储实例（降级模式）
        _redis: Redis 客户端实例
        _use_memory: 是否使用内存存储模式
    """
    
    def __init__(self, storage: Optional[InMemoryStorage] = None):
        """初始化限流服务
        
        Args:
            storage: 存储后端实例，如果提供则直接使用内存存储模式
        """
        self._storage: Optional[InMemoryStorage] = storage
        self._redis = None
        self._use_memory = storage is not None
        self._key_prefix = "popgraph:rate_limit:"

    async def _get_storage(self) -> Union[InMemoryStorage, "redis.Redis"]:
        """获取存储后端（支持 Redis 降级到内存）
        
        Returns:
            存储后端实例（Redis 或 InMemoryStorage）
        """
        if self._use_memory:
            if self._storage is None:
                self._storage = InMemoryStorage()
            return self._storage
        
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                # Redis 不可用，降级到内存存储
                self._storage = InMemoryStorage()
                self._use_memory = True
                return self._storage
        
        return self._redis
    
    def _get_user_key(self, user_id: str) -> str:
        """生成用户的存储 key
        
        Key 格式: popgraph:rate_limit:{user_id}:{date}
        每天使用不同的 key，自动实现跨日重置
        
        Args:
            user_id: 用户ID
            
        Returns:
            存储 key 字符串
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{self._key_prefix}{user_id}:{today}"

    def _get_reset_time(self) -> datetime:
        """获取配额重置时间（次日 UTC 00:00）
        
        Returns:
            配额重置的 datetime 对象
        """
        now = datetime.now(timezone.utc)
        tomorrow = now.date() + timedelta(days=1)
        return datetime(
            year=tomorrow.year,
            month=tomorrow.month,
            day=tomorrow.day,
            hour=0,
            minute=0,
            second=0,
            tzinfo=timezone.utc
        )
    
    def _get_daily_limit(self, tier: MembershipTier) -> int:
        """获取会员等级对应的每日限额
        
        Args:
            tier: 会员等级
            
        Returns:
            每日限额，-1 表示无限
        """
        config = RATE_LIMIT_CONFIG.get(tier, RATE_LIMIT_CONFIG[MembershipTier.FREE])
        return config["daily_limit"]
    
    async def check_limit(self, user_id: str, tier: MembershipTier) -> RateLimitResult:
        """检查用户是否超出限额
        
        Args:
            user_id: 用户ID
            tier: 用户会员等级
            
        Returns:
            RateLimitResult: 限流结果，包含是否允许、剩余配额和重置时间
            
        Requirements: 7.2 - 免费用户每日限额检查
        """
        daily_limit = self._get_daily_limit(tier)
        
        # 专业会员无限制
        if daily_limit == -1:
            return RateLimitResult(
                allowed=True,
                remaining_quota=-1,
                reset_time=None
            )
        
        storage = await self._get_storage()
        key = self._get_user_key(user_id)
        
        # 获取当前使用次数
        current_count_str = await storage.get(key)
        current_count = int(current_count_str) if current_count_str else 0
        
        remaining = max(0, daily_limit - current_count)
        reset_time = self._get_reset_time()
        
        # 检查是否超出限额
        if current_count >= daily_limit:
            return RateLimitResult(
                allowed=False,
                remaining_quota=0,
                reset_time=reset_time
            )
        
        return RateLimitResult(
            allowed=True,
            remaining_quota=remaining,
            reset_time=reset_time
        )

    async def increment_usage(self, user_id: str) -> int:
        """增加用户使用次数
        
        Args:
            user_id: 用户ID
            
        Returns:
            增加后的使用次数
        """
        storage = await self._get_storage()
        key = self._get_user_key(user_id)
        
        # 使用 INCR 原子操作增加计数
        new_count = await storage.incr(key)
        
        # 如果是新 key，设置过期时间为次日 00:00
        if new_count == 1:
            reset_time = self._get_reset_time()
            ttl_seconds = int((reset_time - datetime.now(timezone.utc)).total_seconds())
            if ttl_seconds > 0:
                await storage.expire(key, ttl_seconds)
        
        return new_count
    
    async def get_remaining_quota(self, user_id: str, tier: MembershipTier) -> int:
        """获取用户剩余配额
        
        Args:
            user_id: 用户ID
            tier: 用户会员等级
            
        Returns:
            剩余配额，-1 表示无限
        """
        daily_limit = self._get_daily_limit(tier)
        
        # 专业会员无限制
        if daily_limit == -1:
            return -1
        
        storage = await self._get_storage()
        key = self._get_user_key(user_id)
        
        current_count_str = await storage.get(key)
        current_count = int(current_count_str) if current_count_str else 0
        
        return max(0, daily_limit - current_count)
    
    async def get_current_usage(self, user_id: str) -> int:
        """获取用户当前使用次数
        
        Args:
            user_id: 用户ID
            
        Returns:
            当前使用次数
        """
        storage = await self._get_storage()
        key = self._get_user_key(user_id)
        
        current_count_str = await storage.get(key)
        return int(current_count_str) if current_count_str else 0
    
    async def reset_usage(self, user_id: str) -> None:
        """重置用户使用次数（管理功能）
        
        Args:
            user_id: 用户ID
        """
        storage = await self._get_storage()
        key = self._get_user_key(user_id)
        await storage.delete(key)
    
    async def close(self) -> None:
        """关闭连接"""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


# 创建默认的全局实例
_default_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """获取默认的限流服务实例（单例模式）
    
    Returns:
        RateLimiter 实例
    """
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter()
    return _default_limiter
