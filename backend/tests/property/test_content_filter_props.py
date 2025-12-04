"""Property-based tests for ContentFilterService.

**Feature: popgraph, Property 7: 敏感词过滤有效性**

This module tests that the ContentFilterService correctly identifies and
blocks content containing sensitive keywords from the blocklist.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hypothesis import given, settings, strategies as st, assume

from app.services.content_filter import ContentFilterService


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating random sensitive keywords (non-empty strings)
sensitive_keyword = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    + "".join(chr(i) for i in range(0x4E00, 0x9FA5)),  # Chinese characters
    min_size=2,
    max_size=20,
).filter(lambda x: x.strip() and len(x.strip()) >= 2)

# Strategy for generating a list of sensitive keywords (blocklist)
blocklist_strategy = st.lists(
    sensitive_keyword,
    min_size=1,
    max_size=10,
    unique=True,
)

# Strategy for generating safe text (text that won't accidentally contain keywords)
safe_text_chars = st.text(
    alphabet="0123456789!@#$%^&*()_+-=[]{}|;':\",./<>? \n\t",
    min_size=0,
    max_size=50,
)

# Strategy for generating prefix/suffix text around sensitive keywords
surrounding_text = st.text(
    alphabet="0123456789!@#$%^&*()_+-=[]{}|;':\",./<>? ",
    min_size=0,
    max_size=30,
)


# ============================================================================
# Property 7: 敏感词过滤有效性
# **Feature: popgraph, Property 7: 敏感词过滤有效性**
# **Validates: Requirements 6.1**
#
# For any user input containing keywords from the blocklist, the content
# filter SHALL return is_allowed = False and include the matched keywords
# in blocked_keywords array.
# ============================================================================


@settings(max_examples=100)
@given(
    blocklist=blocklist_strategy,
    keyword_index=st.integers(min_value=0, max_value=100),
    prefix=surrounding_text,
    suffix=surrounding_text,
)
def test_content_with_blocklist_keyword_is_rejected(
    blocklist: list[str],
    keyword_index: int,
    prefix: str,
    suffix: str,
) -> None:
    """
    **Feature: popgraph, Property 7: 敏感词过滤有效性**
    **Validates: Requirements 6.1**
    
    Property: For any input text containing a keyword from the blocklist,
    the content filter must return is_allowed = False.
    """
    # Arrange
    # Select a keyword from the blocklist using modulo to handle index bounds
    keyword = blocklist[keyword_index % len(blocklist)]
    
    # Create input text containing the sensitive keyword
    input_text = f"{prefix}{keyword}{suffix}"
    
    # Create filter with the custom blocklist
    filter_service = ContentFilterService(blocklist=set(blocklist))
    
    # Act
    result = filter_service.check_content(input_text)
    
    # Assert: Content should be rejected
    assert result.is_allowed is False, (
        f"Content containing blocklist keyword '{keyword}' should be rejected. "
        f"Input: '{input_text}', Result: is_allowed={result.is_allowed}"
    )


@settings(max_examples=100)
@given(
    blocklist=blocklist_strategy,
    keyword_index=st.integers(min_value=0, max_value=100),
    prefix=surrounding_text,
    suffix=surrounding_text,
)
def test_blocked_keywords_array_contains_matched_keyword(
    blocklist: list[str],
    keyword_index: int,
    prefix: str,
    suffix: str,
) -> None:
    """
    **Feature: popgraph, Property 7: 敏感词过滤有效性**
    **Validates: Requirements 6.1**
    
    Property: For any input text containing a keyword from the blocklist,
    the blocked_keywords array must include the matched keyword.
    """
    # Arrange
    keyword = blocklist[keyword_index % len(blocklist)]
    input_text = f"{prefix}{keyword}{suffix}"
    filter_service = ContentFilterService(blocklist=set(blocklist))
    
    # Act
    result = filter_service.check_content(input_text)
    
    # Assert: The matched keyword should be in blocked_keywords
    # Note: The filter uses case-insensitive matching, so we check case-insensitively
    blocked_lower = [k.lower() for k in result.blocked_keywords]
    assert keyword.lower() in blocked_lower, (
        f"Matched keyword '{keyword}' should be in blocked_keywords. "
        f"Got: {result.blocked_keywords}"
    )


@settings(max_examples=100)
@given(
    blocklist=blocklist_strategy,
    safe_text=safe_text_chars,
)
def test_content_without_blocklist_keywords_is_allowed(
    blocklist: list[str],
    safe_text: str,
) -> None:
    """
    **Feature: popgraph, Property 7: 敏感词过滤有效性**
    **Validates: Requirements 6.1**
    
    Property: For any input text that does NOT contain any keyword from
    the blocklist, the content filter must return is_allowed = True.
    """
    # Arrange
    filter_service = ContentFilterService(blocklist=set(blocklist))
    
    # Ensure the safe_text doesn't accidentally contain any blocklist keyword
    for keyword in blocklist:
        assume(keyword.lower() not in safe_text.lower())
    
    # Act
    result = filter_service.check_content(safe_text)
    
    # Assert: Content should be allowed
    assert result.is_allowed is True, (
        f"Content without blocklist keywords should be allowed. "
        f"Input: '{safe_text}', Blocklist: {blocklist}, "
        f"Result: is_allowed={result.is_allowed}, blocked={result.blocked_keywords}"
    )


@settings(max_examples=100)
@given(
    blocklist=blocklist_strategy,
    safe_text=safe_text_chars,
)
def test_allowed_content_has_empty_blocked_keywords(
    blocklist: list[str],
    safe_text: str,
) -> None:
    """
    **Feature: popgraph, Property 7: 敏感词过滤有效性**
    **Validates: Requirements 6.1**
    
    Property: For any input text that is allowed, the blocked_keywords
    array must be empty.
    """
    # Arrange
    filter_service = ContentFilterService(blocklist=set(blocklist))
    
    # Ensure the safe_text doesn't contain any blocklist keyword
    for keyword in blocklist:
        assume(keyword.lower() not in safe_text.lower())
    
    # Act
    result = filter_service.check_content(safe_text)
    
    # Assert: blocked_keywords should be empty for allowed content
    assert len(result.blocked_keywords) == 0, (
        f"Allowed content should have empty blocked_keywords. "
        f"Input: '{safe_text}', Got: {result.blocked_keywords}"
    )


@settings(max_examples=100)
@given(
    blocklist=blocklist_strategy,
    num_keywords_to_include=st.integers(min_value=1, max_value=3),
    separator=st.sampled_from([" ", ", ", " - ", "\n", "。"]),
)
def test_multiple_blocklist_keywords_all_detected(
    blocklist: list[str],
    num_keywords_to_include: int,
    separator: str,
) -> None:
    """
    **Feature: popgraph, Property 7: 敏感词过滤有效性**
    **Validates: Requirements 6.1**
    
    Property: For any input text containing multiple keywords from the
    blocklist, all matched keywords should be detected and included in
    the blocked_keywords array.
    """
    # Arrange
    # Select multiple keywords from blocklist
    num_to_use = min(num_keywords_to_include, len(blocklist))
    keywords_to_include = blocklist[:num_to_use]
    
    # Create input text with multiple sensitive keywords
    input_text = separator.join(keywords_to_include)
    
    filter_service = ContentFilterService(blocklist=set(blocklist))
    
    # Act
    result = filter_service.check_content(input_text)
    
    # Assert: Content should be rejected
    assert result.is_allowed is False, (
        f"Content with multiple blocklist keywords should be rejected. "
        f"Input: '{input_text}'"
    )
    
    # Assert: All included keywords should be detected
    blocked_lower = [k.lower() for k in result.blocked_keywords]
    for keyword in keywords_to_include:
        assert keyword.lower() in blocked_lower, (
            f"Keyword '{keyword}' should be detected. "
            f"Input: '{input_text}', Got blocked: {result.blocked_keywords}"
        )


@settings(max_examples=100)
@given(
    blocklist=blocklist_strategy,
    keyword_index=st.integers(min_value=0, max_value=100),
)
def test_case_insensitive_matching(
    blocklist: list[str],
    keyword_index: int,
) -> None:
    """
    **Feature: popgraph, Property 7: 敏感词过滤有效性**
    **Validates: Requirements 6.1**
    
    Property: The content filter should match keywords case-insensitively
    for English text.
    """
    # Arrange
    keyword = blocklist[keyword_index % len(blocklist)]
    
    # Skip if keyword has no alphabetic characters (case doesn't apply)
    assume(any(c.isalpha() for c in keyword))
    
    # Create variations: uppercase, lowercase, mixed case
    variations = [
        keyword.upper(),
        keyword.lower(),
        keyword.swapcase(),
    ]
    
    filter_service = ContentFilterService(blocklist=set(blocklist))
    
    # Act & Assert: All case variations should be detected
    for variation in variations:
        result = filter_service.check_content(variation)
        assert result.is_allowed is False, (
            f"Case variation '{variation}' of keyword '{keyword}' should be blocked. "
            f"Result: is_allowed={result.is_allowed}"
        )

