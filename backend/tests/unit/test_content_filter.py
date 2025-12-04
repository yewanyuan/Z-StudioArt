"""Unit tests for ContentFilterService.

This module tests the content filter service with specific examples
to verify that known sensitive keywords are correctly filtered and
normal content passes through.

Requirements: 6.1 - WHEN a user submits input containing sensitive keywords 
THEN the PopGraph System SHALL reject the request and display an appropriate warning message
"""

import sys
from pathlib import Path

import pytest

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.content_filter import (
    ContentFilterService,
    DEFAULT_BLOCKLIST,
    get_content_filter,
)


class TestContentFilterWithKnownSensitiveWords:
    """测试已知敏感词被正确过滤"""

    def test_chinese_sensitive_word_gambling_is_blocked(self) -> None:
        """测试中文敏感词"赌博"被正确过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("这是一个赌博网站")
        
        assert result.is_allowed is False
        assert "赌博" in result.blocked_keywords
        assert result.warning_message is not None

    def test_chinese_sensitive_word_drugs_is_blocked(self) -> None:
        """测试中文敏感词"毒品"被正确过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("毒品交易")
        
        assert result.is_allowed is False
        assert "毒品" in result.blocked_keywords

    def test_chinese_sensitive_word_porn_is_blocked(self) -> None:
        """测试中文敏感词"色情"被正确过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("色情内容")
        
        assert result.is_allowed is False
        assert "色情" in result.blocked_keywords

    def test_english_sensitive_word_gambling_is_blocked(self) -> None:
        """测试英文敏感词"gambling"被正确过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("online gambling site")
        
        assert result.is_allowed is False
        assert "gambling" in [k.lower() for k in result.blocked_keywords]

    def test_english_sensitive_word_drugs_is_blocked(self) -> None:
        """测试英文敏感词"drugs"被正确过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("illegal drugs")
        
        assert result.is_allowed is False
        assert "drugs" in [k.lower() for k in result.blocked_keywords]

    def test_english_sensitive_word_case_insensitive(self) -> None:
        """测试英文敏感词大小写不敏感"""
        filter_service = ContentFilterService()
        
        # 测试大写
        result_upper = filter_service.check_content("GAMBLING")
        assert result_upper.is_allowed is False
        
        # 测试混合大小写
        result_mixed = filter_service.check_content("GaMbLiNg")
        assert result_mixed.is_allowed is False

    def test_multiple_sensitive_words_all_detected(self) -> None:
        """测试多个敏感词同时出现时都被检测到"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("赌博和毒品都是违法的")
        
        assert result.is_allowed is False
        assert len(result.blocked_keywords) >= 2
        blocked_lower = [k.lower() for k in result.blocked_keywords]
        assert "赌博" in blocked_lower
        assert "毒品" in blocked_lower

    def test_sensitive_word_embedded_in_text(self) -> None:
        """测试敏感词嵌入在正常文本中也能被检测"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("今天天气很好，但是赌博是不对的行为")
        
        assert result.is_allowed is False
        assert "赌博" in result.blocked_keywords


class TestContentFilterWithNormalContent:
    """测试正常内容通过过滤"""

    def test_normal_chinese_text_is_allowed(self) -> None:
        """测试正常中文文本通过过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("今天天气真好，适合出去散步")
        
        assert result.is_allowed is True
        assert len(result.blocked_keywords) == 0
        assert result.warning_message is None

    def test_normal_english_text_is_allowed(self) -> None:
        """测试正常英文文本通过过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("This is a beautiful day for shopping")
        
        assert result.is_allowed is True
        assert len(result.blocked_keywords) == 0

    def test_marketing_text_is_allowed(self) -> None:
        """测试正常营销文案通过过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("限时特惠！全场5折起，买一送一！")
        
        assert result.is_allowed is True
        assert len(result.blocked_keywords) == 0

    def test_product_description_is_allowed(self) -> None:
        """测试正常商品描述通过过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("高品质纯棉T恤，舒适透气，多色可选")
        
        assert result.is_allowed is True
        assert len(result.blocked_keywords) == 0

    def test_empty_text_is_allowed(self) -> None:
        """测试空文本通过过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("")
        
        assert result.is_allowed is True
        assert len(result.blocked_keywords) == 0

    def test_whitespace_only_text_is_allowed(self) -> None:
        """测试纯空白文本通过过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("   \n\t  ")
        
        assert result.is_allowed is True
        assert len(result.blocked_keywords) == 0

    def test_numbers_and_symbols_are_allowed(self) -> None:
        """测试数字和符号通过过滤"""
        filter_service = ContentFilterService()
        result = filter_service.check_content("价格：¥99.99 - 50% OFF!")
        
        assert result.is_allowed is True
        assert len(result.blocked_keywords) == 0


class TestContentFilterBlocklistManagement:
    """测试敏感词列表管理功能"""

    def test_add_to_blocklist(self) -> None:
        """测试添加敏感词到黑名单"""
        filter_service = ContentFilterService(blocklist=set())
        
        # 初始时应该允许
        result_before = filter_service.check_content("测试词")
        assert result_before.is_allowed is True
        
        # 添加敏感词后应该被阻止
        filter_service.add_to_blocklist(["测试词"])
        result_after = filter_service.check_content("测试词")
        assert result_after.is_allowed is False

    def test_remove_from_blocklist(self) -> None:
        """测试从黑名单移除敏感词"""
        filter_service = ContentFilterService(blocklist={"测试词"})
        
        # 初始时应该被阻止
        result_before = filter_service.check_content("测试词")
        assert result_before.is_allowed is False
        
        # 移除敏感词后应该允许
        filter_service.remove_from_blocklist(["测试词"])
        result_after = filter_service.check_content("测试词")
        assert result_after.is_allowed is True

    def test_custom_blocklist(self) -> None:
        """测试使用自定义敏感词列表"""
        custom_blocklist = {"自定义词1", "自定义词2"}
        filter_service = ContentFilterService(blocklist=custom_blocklist)
        
        # 自定义词应该被阻止
        result1 = filter_service.check_content("自定义词1")
        assert result1.is_allowed is False
        
        # 默认敏感词不应该被阻止（因为使用了自定义列表）
        result2 = filter_service.check_content("赌博")
        assert result2.is_allowed is True

    def test_empty_blocklist_allows_all(self) -> None:
        """测试空敏感词列表允许所有内容"""
        filter_service = ContentFilterService(blocklist=set())
        
        result = filter_service.check_content("赌博毒品色情")
        assert result.is_allowed is True


class TestContentFilterSingleton:
    """测试单例模式"""

    def test_get_content_filter_returns_same_instance(self) -> None:
        """测试 get_content_filter 返回相同实例"""
        filter1 = get_content_filter()
        filter2 = get_content_filter()
        
        assert filter1 is filter2

    def test_default_filter_uses_default_blocklist(self) -> None:
        """测试默认过滤器使用默认敏感词列表"""
        filter_service = get_content_filter()
        
        # 验证默认敏感词被过滤
        result = filter_service.check_content("赌博")
        assert result.is_allowed is False
