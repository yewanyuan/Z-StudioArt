"""Membership Service for PopGraph.

This module implements membership-related business logic including
watermark rules, feature access permissions, and subscription expiry management.

Requirements:
- 7.1: WHEN a free-tier user generates a poster THEN the PopGraph System 
       SHALL add a visible watermark to the output image
- 7.3: WHEN a basic member generates a poster THEN the PopGraph System 
       SHALL produce output without watermark and with priority processing
- 7.4: WHEN a professional member requests scene fusion feature THEN the 
       PopGraph System SHALL grant access to the product visualization functionality
- 4.7: WHEN a subscription expires THEN THE Subscription_Service SHALL 
       downgrade the user to FREE tier
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, TYPE_CHECKING

from app.models.schemas import MembershipTier

if TYPE_CHECKING:
    from app.models.database import User


logger = logging.getLogger(__name__)


class Feature(str, Enum):
    """可用功能枚举"""
    POSTER_GENERATION = "poster_generation"      # 海报生成
    SCENE_FUSION = "scene_fusion"                # 场景融合
    BATCH_GENERATION = "batch_generation"        # 批量生成
    PRIORITY_PROCESSING = "priority_processing"  # 优先处理
    NO_WATERMARK = "no_watermark"                # 无水印


# 会员功能权限配置
# 定义每个会员等级可以访问的功能
MEMBERSHIP_FEATURES: dict[MembershipTier, set[Feature]] = {
    MembershipTier.FREE: {
        Feature.POSTER_GENERATION,
        Feature.BATCH_GENERATION,
    },
    MembershipTier.BASIC: {
        Feature.POSTER_GENERATION,
        Feature.BATCH_GENERATION,
        Feature.PRIORITY_PROCESSING,
        Feature.NO_WATERMARK,
    },
    MembershipTier.PROFESSIONAL: {
        Feature.POSTER_GENERATION,
        Feature.BATCH_GENERATION,
        Feature.PRIORITY_PROCESSING,
        Feature.NO_WATERMARK,
        Feature.SCENE_FUSION,
    },
}


@dataclass
class WatermarkRule:
    """水印规则结果"""
    should_add_watermark: bool
    watermark_text: Optional[str] = None
    watermark_opacity: float = 0.5


@dataclass
class FeatureAccessResult:
    """功能访问权限结果"""
    allowed: bool
    required_tier: Optional[MembershipTier] = None
    message: Optional[str] = None


class MembershipService:
    """会员权限服务
    
    负责处理会员相关的业务逻辑，包括：
    - 水印规则判断
    - 功能权限检查
    
    Attributes:
        watermark_text: 水印文本内容
    """
    
    DEFAULT_WATERMARK_TEXT = "PopGraph"
    DEFAULT_WATERMARK_OPACITY = 0.5
    
    def __init__(self, watermark_text: str = DEFAULT_WATERMARK_TEXT):
        """初始化会员服务
        
        Args:
            watermark_text: 水印文本，默认为 "PopGraph"
        """
        self._watermark_text = watermark_text
    
    def should_add_watermark(self, tier: MembershipTier) -> bool:
        """判断是否需要添加水印
        
        根据会员等级判断生成的图像是否需要添加水印。
        
        Args:
            tier: 用户会员等级
            
        Returns:
            True 如果需要添加水印，False 如果不需要
            
        Requirements:
            - 7.1: 免费用户生成的海报需要添加水印
            - 7.3: 基础会员和专业会员生成的海报无水印
        """
        # 只有免费用户需要添加水印
        return tier == MembershipTier.FREE
    
    def get_watermark_rule(self, tier: MembershipTier) -> WatermarkRule:
        """获取水印规则详情
        
        Args:
            tier: 用户会员等级
            
        Returns:
            WatermarkRule: 包含是否添加水印、水印文本和透明度的规则
        """
        if self.should_add_watermark(tier):
            return WatermarkRule(
                should_add_watermark=True,
                watermark_text=self._watermark_text,
                watermark_opacity=self.DEFAULT_WATERMARK_OPACITY
            )
        return WatermarkRule(should_add_watermark=False)
    
    def has_feature_access(self, tier: MembershipTier, feature: Feature) -> bool:
        """检查会员是否有权访问指定功能
        
        Args:
            tier: 用户会员等级
            feature: 要检查的功能
            
        Returns:
            True 如果有权访问，False 如果无权访问
            
        Requirements:
            - 7.4: 只有专业会员可以访问场景融合功能
        """
        allowed_features = MEMBERSHIP_FEATURES.get(tier, set())
        return feature in allowed_features
    
    def check_feature_access(
        self, 
        tier: MembershipTier, 
        feature: Feature
    ) -> FeatureAccessResult:
        """检查功能访问权限并返回详细结果
        
        Args:
            tier: 用户会员等级
            feature: 要检查的功能
            
        Returns:
            FeatureAccessResult: 包含是否允许、所需等级和提示消息
        """
        if self.has_feature_access(tier, feature):
            return FeatureAccessResult(allowed=True)
        
        # 查找需要哪个等级才能访问该功能
        required_tier = self._find_minimum_tier_for_feature(feature)
        
        return FeatureAccessResult(
            allowed=False,
            required_tier=required_tier,
            message=self._get_upgrade_message(feature, required_tier)
        )
    
    def can_access_scene_fusion(self, tier: MembershipTier) -> bool:
        """检查是否可以访问场景融合功能
        
        这是一个便捷方法，专门用于检查场景融合功能的访问权限。
        
        Args:
            tier: 用户会员等级
            
        Returns:
            True 如果可以访问场景融合，False 如果不能
            
        Requirements:
            - 7.4: 只有专业会员可以访问场景融合功能
        """
        return self.has_feature_access(tier, Feature.SCENE_FUSION)
    
    def has_priority_processing(self, tier: MembershipTier) -> bool:
        """检查是否享有优先处理
        
        Args:
            tier: 用户会员等级
            
        Returns:
            True 如果享有优先处理，False 如果不享有
            
        Requirements:
            - 7.3: 基础会员享有优先处理
        """
        return self.has_feature_access(tier, Feature.PRIORITY_PROCESSING)
    
    def _find_minimum_tier_for_feature(self, feature: Feature) -> Optional[MembershipTier]:
        """查找访问指定功能所需的最低会员等级
        
        Args:
            feature: 要查找的功能
            
        Returns:
            最低所需会员等级，如果没有任何等级可以访问则返回 None
        """
        # 按等级从低到高检查
        tier_order = [
            MembershipTier.FREE,
            MembershipTier.BASIC,
            MembershipTier.PROFESSIONAL
        ]
        
        for tier in tier_order:
            if feature in MEMBERSHIP_FEATURES.get(tier, set()):
                return tier
        
        return None
    
    def _get_upgrade_message(
        self, 
        feature: Feature, 
        required_tier: Optional[MembershipTier]
    ) -> str:
        """生成升级提示消息
        
        Args:
            feature: 被拒绝访问的功能
            required_tier: 所需的会员等级
            
        Returns:
            用户友好的升级提示消息
        """
        feature_names = {
            Feature.POSTER_GENERATION: "海报生成",
            Feature.SCENE_FUSION: "场景融合",
            Feature.BATCH_GENERATION: "批量生成",
            Feature.PRIORITY_PROCESSING: "优先处理",
            Feature.NO_WATERMARK: "无水印输出",
        }
        
        tier_names = {
            MembershipTier.FREE: "免费版",
            MembershipTier.BASIC: "基础会员",
            MembershipTier.PROFESSIONAL: "专业会员",
        }
        
        feature_name = feature_names.get(feature, str(feature))
        
        if required_tier is None:
            return f"功能 {feature_name} 当前不可用"
        
        tier_name = tier_names.get(required_tier, str(required_tier))
        return f"升级到{tier_name}即可使用{feature_name}功能"
    
    def get_tier_features(self, tier: MembershipTier) -> set[Feature]:
        """获取指定会员等级可用的所有功能
        
        Args:
            tier: 会员等级
            
        Returns:
            该等级可用的功能集合
        """
        return MEMBERSHIP_FEATURES.get(tier, set()).copy()
    
    # ========================================================================
    # Subscription Expiry Management
    # ========================================================================
    
    def is_subscription_expired(self, user: "User") -> bool:
        """检查用户订阅是否已过期
        
        Args:
            user: 用户对象
            
        Returns:
            True 如果订阅已过期，False 如果未过期或无订阅
            
        Requirements:
            - 4.7: 检查订阅是否过期
        """
        # FREE 用户没有订阅，不算过期
        if user.membership_tier == MembershipTier.FREE:
            return False
        
        # 没有设置过期时间，视为永久有效（不过期）
        if user.membership_expiry is None:
            return False
        
        # 确保时区一致性
        expiry = user.membership_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        return now > expiry
    
    def check_and_downgrade_if_expired(self, user: "User") -> bool:
        """检查用户订阅并在过期时降级
        
        如果用户订阅已过期，将其降级为 FREE 等级。
        
        Args:
            user: 用户对象
            
        Returns:
            True 如果进行了降级，False 如果未降级
            
        Requirements:
            - 4.7: WHEN a subscription expires THEN THE Subscription_Service 
                   SHALL downgrade the user to FREE tier
        """
        if not self.is_subscription_expired(user):
            return False
        
        old_tier = user.membership_tier
        user.membership_tier = MembershipTier.FREE
        user.updated_at = datetime.now(timezone.utc)
        
        logger.info(
            f"User subscription expired and downgraded: user_id={user.id}, "
            f"old_tier={old_tier.value}, new_tier={MembershipTier.FREE.value}"
        )
        
        return True
    
    def downgrade_to_free(self, user: "User") -> "User":
        """将用户降级为 FREE 等级
        
        Args:
            user: 用户对象
            
        Returns:
            更新后的用户对象
            
        Requirements:
            - 4.7: 订阅过期后降级为 FREE
        """
        user.membership_tier = MembershipTier.FREE
        user.updated_at = datetime.now(timezone.utc)
        
        logger.info(
            f"User downgraded to FREE: user_id={user.id}"
        )
        
        return user
    
    def check_expired_users(self, users: list["User"]) -> list["User"]:
        """批量检查并降级过期用户
        
        用于定时任务批量处理过期订阅。
        
        Args:
            users: 用户列表
            
        Returns:
            被降级的用户列表
            
        Requirements:
            - 4.7: 定时检查过期订阅并降级
        """
        downgraded_users = []
        
        for user in users:
            if self.check_and_downgrade_if_expired(user):
                downgraded_users.append(user)
        
        if downgraded_users:
            logger.info(
                f"Batch expiry check completed: {len(downgraded_users)} users downgraded"
            )
        
        return downgraded_users


# 创建默认的全局实例
_default_service: Optional[MembershipService] = None


def get_membership_service() -> MembershipService:
    """获取默认的会员服务实例（单例模式）
    
    Returns:
        MembershipService 实例
    """
    global _default_service
    if _default_service is None:
        _default_service = MembershipService()
    return _default_service
