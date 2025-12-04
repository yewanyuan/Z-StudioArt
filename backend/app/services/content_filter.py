"""Content Filter Service for PopGraph.

This module implements sensitive content filtering functionality.

Requirements: 6.1 - WHEN a user submits input containing sensitive keywords 
THEN the PopGraph System SHALL reject the request and display an appropriate warning message
"""

import re
from pathlib import Path
from typing import Optional

from app.models.schemas import ContentFilterResult


# 默认敏感词列表（可通过外部文件扩展）
DEFAULT_BLOCKLIST: set[str] = {
    # 政治敏感词
    "政治敏感词1",
    "政治敏感词2",
    # 违法内容
    "赌博",
    "毒品",
    "枪支",
    # 色情内容
    "色情",
    "淫秽",
    # 暴力内容
    "暴力",
    "恐怖",
    # 欺诈内容
    "诈骗",
    "传销",
    # 英文敏感词
    "gambling",
    "drugs",
    "porn",
    "violence",
    "terrorism",
    "fraud",
}


class ContentFilterService:
    """敏感内容过滤服务
    
    负责检查用户输入是否包含敏感词，并返回过滤结果。
    
    Attributes:
        blocklist: 敏感词集合
    """
    
    def __init__(self, blocklist: Optional[set[str]] = None):
        """初始化内容过滤服务
        
        Args:
            blocklist: 自定义敏感词集合，如果为 None 则使用默认列表
        """
        self._blocklist: set[str] = blocklist if blocklist is not None else DEFAULT_BLOCKLIST.copy()
        # 预编译正则表达式以提高匹配效率
        self._pattern: Optional[re.Pattern] = self._compile_pattern()
    
    def _compile_pattern(self) -> Optional[re.Pattern]:
        """编译敏感词正则表达式
        
        Returns:
            编译后的正则表达式，如果敏感词列表为空则返回 None
        """
        if not self._blocklist:
            return None
        # 对敏感词进行转义，避免正则特殊字符问题
        escaped_keywords = [re.escape(keyword) for keyword in self._blocklist]
        # 使用 | 连接所有敏感词，忽略大小写
        pattern_str = "|".join(escaped_keywords)
        return re.compile(pattern_str, re.IGNORECASE)
    
    @property
    def blocklist(self) -> set[str]:
        """获取当前敏感词列表"""
        return self._blocklist.copy()
    
    def check_content(self, text: str) -> ContentFilterResult:
        """检查文本内容是否包含敏感词
        
        Args:
            text: 待检查的文本内容
            
        Returns:
            ContentFilterResult: 过滤结果，包含是否允许、被阻止的关键词和警告消息
            
        Requirements: 6.1 - 敏感词过滤
        """
        if not text or not text.strip():
            return ContentFilterResult(
                is_allowed=True,
                blocked_keywords=[],
                warning_message=None
            )
        
        if self._pattern is None:
            return ContentFilterResult(
                is_allowed=True,
                blocked_keywords=[],
                warning_message=None
            )
        
        # 查找所有匹配的敏感词
        matches = self._pattern.findall(text)
        
        if not matches:
            return ContentFilterResult(
                is_allowed=True,
                blocked_keywords=[],
                warning_message=None
            )
        
        # 去重并保持原始大小写
        blocked_keywords = list(set(matches))
        
        return ContentFilterResult(
            is_allowed=False,
            blocked_keywords=blocked_keywords,
            warning_message=f"内容包含敏感词，请修改后重试。检测到的敏感词: {', '.join(blocked_keywords)}"
        )
    
    def add_to_blocklist(self, keywords: list[str]) -> None:
        """添加敏感词到黑名单
        
        Args:
            keywords: 要添加的敏感词列表
        """
        self._blocklist.update(keywords)
        self._pattern = self._compile_pattern()
    
    def remove_from_blocklist(self, keywords: list[str]) -> None:
        """从黑名单移除敏感词
        
        Args:
            keywords: 要移除的敏感词列表
        """
        self._blocklist -= set(keywords)
        self._pattern = self._compile_pattern()
    
    def load_blocklist_from_file(self, file_path: str) -> int:
        """从文件加载敏感词列表
        
        文件格式：每行一个敏感词，空行和以 # 开头的行会被忽略
        
        Args:
            file_path: 敏感词文件路径
            
        Returns:
            加载的敏感词数量
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"敏感词文件不存在: {file_path}")
        
        loaded_count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                keyword = line.strip()
                # 跳过空行和注释行
                if keyword and not keyword.startswith("#"):
                    self._blocklist.add(keyword)
                    loaded_count += 1
        
        # 重新编译正则表达式
        self._pattern = self._compile_pattern()
        return loaded_count
    
    def clear_blocklist(self) -> None:
        """清空敏感词列表"""
        self._blocklist.clear()
        self._pattern = None


# 创建默认的全局实例
_default_filter: Optional[ContentFilterService] = None


def get_content_filter() -> ContentFilterService:
    """获取默认的内容过滤服务实例（单例模式）
    
    Returns:
        ContentFilterService 实例
    """
    global _default_filter
    if _default_filter is None:
        _default_filter = ContentFilterService()
    return _default_filter
