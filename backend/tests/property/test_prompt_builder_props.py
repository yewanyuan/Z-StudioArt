"""Property-based tests for PromptBuilder.

**Feature: popgraph, Property 1: 文本渲染正确性**

This module tests that the PromptBuilder correctly embeds user-provided
marketing text into the generated prompt without modification.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hypothesis import given, settings, strategies as st

from app.models.schemas import PosterGenerationRequest, PromptModifiers
from app.utils.prompt_builder import PromptBuilder


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Chinese character ranges (common CJK characters)
chinese_chars = st.text(
    alphabet="".join(chr(i) for i in range(0x4E00, 0x9FFF)),
    min_size=1,
    max_size=50,
)

# English text (ASCII letters, numbers, spaces, common punctuation)
english_chars = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 !?.,",
    min_size=1,
    max_size=50,
)

# Mixed text (both Chinese and English)
mixed_text = st.one_of(chinese_chars, english_chars)

# Scene description strategy
scene_description = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 "
    + "".join(chr(i) for i in range(0x4E00, 0x9FA5)),
    min_size=1,
    max_size=100,
)

# Aspect ratio strategy
aspect_ratio = st.sampled_from(["1:1", "9:16", "16:9"])

# Batch size strategy
batch_size = st.sampled_from([1, 4])


# ============================================================================
# Property 1: 文本渲染正确性
# **Feature: popgraph, Property 1: 文本渲染正确性**
# **Validates: Requirements 1.1, 1.2**
#
# For any valid poster generation request with marketing text (Chinese or 
# English), the generated prompt SHALL contain the exact user-provided text
# without modification.
# ============================================================================


@settings(max_examples=100)
@given(
    marketing_text=chinese_chars,
    scene_desc=scene_description,
    ratio=aspect_ratio,
    batch=batch_size,
)
def test_chinese_text_preserved_in_prompt(
    marketing_text: str,
    scene_desc: str,
    ratio: str,
    batch: int,
) -> None:
    """
    **Feature: popgraph, Property 1: 文本渲染正确性**
    **Validates: Requirements 1.1**
    
    Property: For any Chinese marketing text, the generated prompt must
    contain the exact text without modification.
    """
    # Arrange
    builder = PromptBuilder()
    request = PosterGenerationRequest(
        scene_description=scene_desc,
        marketing_text=marketing_text,
        language="zh",
        aspect_ratio=ratio,
        batch_size=batch,
    )
    
    # Act
    prompt = builder.build_poster_prompt(request)
    
    # Assert: The exact marketing text must appear in the prompt
    assert marketing_text in prompt, (
        f"Chinese marketing text '{marketing_text}' not found in prompt: {prompt}"
    )


@settings(max_examples=100)
@given(
    marketing_text=english_chars,
    scene_desc=scene_description,
    ratio=aspect_ratio,
    batch=batch_size,
)
def test_english_text_preserved_in_prompt(
    marketing_text: str,
    scene_desc: str,
    ratio: str,
    batch: int,
) -> None:
    """
    **Feature: popgraph, Property 1: 文本渲染正确性**
    **Validates: Requirements 1.2**
    
    Property: For any English marketing text, the generated prompt must
    contain the exact text without modification.
    """
    # Arrange
    builder = PromptBuilder()
    request = PosterGenerationRequest(
        scene_description=scene_desc,
        marketing_text=marketing_text,
        language="en",
        aspect_ratio=ratio,
        batch_size=batch,
    )
    
    # Act
    prompt = builder.build_poster_prompt(request)
    
    # Assert: The exact marketing text must appear in the prompt
    assert marketing_text in prompt, (
        f"English marketing text '{marketing_text}' not found in prompt: {prompt}"
    )


@settings(max_examples=100)
@given(
    text=mixed_text,
    language=st.sampled_from(["zh", "en"]),
)
def test_inject_text_placement_preserves_text(
    text: str,
    language: str,
) -> None:
    """
    **Feature: popgraph, Property 1: 文本渲染正确性**
    **Validates: Requirements 1.1, 1.2**
    
    Property: The inject_text_placement method must preserve the exact
    text in its output regardless of language setting.
    """
    # Arrange
    builder = PromptBuilder()
    
    # Act
    result = builder.inject_text_placement("", text, language)
    
    # Assert: The exact text must appear in the result
    assert text in result, (
        f"Text '{text}' not found in inject_text_placement result: {result}"
    )


# ============================================================================
# Property 4: 模板参数应用正确性
# **Feature: popgraph, Property 4: 模板参数应用正确性**
# **Validates: Requirements 3.1, 3.2, 3.3**
#
# For any template application request, the generated prompt SHALL contain
# all style keywords, color scheme, layout hints, and font style parameters
# defined in the selected template configuration.
# ============================================================================

# Strategy for generating non-empty style keywords
style_keyword = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -_",
    min_size=1,
    max_size=30,
).filter(lambda x: x.strip())  # Ensure non-empty after strip

style_keywords_list = st.lists(style_keyword, min_size=1, max_size=5)

# Strategy for generating non-empty color scheme
color_scheme = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -_#",
    min_size=1,
    max_size=30,
).filter(lambda x: x.strip())

# Strategy for generating non-empty layout hints
layout_hints = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -_",
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip())

# Strategy for generating non-empty font style
font_style = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -_",
    min_size=1,
    max_size=30,
).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(
    keywords=style_keywords_list,
    color=color_scheme,
    layout=layout_hints,
    font=font_style,
)
def test_apply_modifiers_contains_all_style_keywords(
    keywords: list[str],
    color: str,
    layout: str,
    font: str,
) -> None:
    """
    **Feature: popgraph, Property 4: 模板参数应用正确性**
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    Property: For any template modifiers, the apply_modifiers output must
    contain all style keywords from the configuration.
    """
    # Arrange
    builder = PromptBuilder()
    modifiers = PromptModifiers(
        style_keywords=keywords,
        color_scheme=color,
        layout_hints=layout,
        font_style=font,
    )
    
    # Act
    result = builder.apply_modifiers(modifiers)
    
    # Assert: All style keywords must appear in the result
    for keyword in keywords:
        assert keyword in result, (
            f"Style keyword '{keyword}' not found in apply_modifiers result: {result}"
        )


@settings(max_examples=100)
@given(
    keywords=style_keywords_list,
    color=color_scheme,
    layout=layout_hints,
    font=font_style,
)
def test_apply_modifiers_contains_color_scheme(
    keywords: list[str],
    color: str,
    layout: str,
    font: str,
) -> None:
    """
    **Feature: popgraph, Property 4: 模板参数应用正确性**
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    Property: For any template modifiers, the apply_modifiers output must
    contain the color scheme from the configuration.
    """
    # Arrange
    builder = PromptBuilder()
    modifiers = PromptModifiers(
        style_keywords=keywords,
        color_scheme=color,
        layout_hints=layout,
        font_style=font,
    )
    
    # Act
    result = builder.apply_modifiers(modifiers)
    
    # Assert: Color scheme must appear in the result
    assert color in result, (
        f"Color scheme '{color}' not found in apply_modifiers result: {result}"
    )


@settings(max_examples=100)
@given(
    keywords=style_keywords_list,
    color=color_scheme,
    layout=layout_hints,
    font=font_style,
)
def test_apply_modifiers_contains_layout_hints(
    keywords: list[str],
    color: str,
    layout: str,
    font: str,
) -> None:
    """
    **Feature: popgraph, Property 4: 模板参数应用正确性**
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    Property: For any template modifiers, the apply_modifiers output must
    contain the layout hints from the configuration.
    """
    # Arrange
    builder = PromptBuilder()
    modifiers = PromptModifiers(
        style_keywords=keywords,
        color_scheme=color,
        layout_hints=layout,
        font_style=font,
    )
    
    # Act
    result = builder.apply_modifiers(modifiers)
    
    # Assert: Layout hints must appear in the result
    assert layout in result, (
        f"Layout hints '{layout}' not found in apply_modifiers result: {result}"
    )


@settings(max_examples=100)
@given(
    keywords=style_keywords_list,
    color=color_scheme,
    layout=layout_hints,
    font=font_style,
)
def test_apply_modifiers_contains_font_style(
    keywords: list[str],
    color: str,
    layout: str,
    font: str,
) -> None:
    """
    **Feature: popgraph, Property 4: 模板参数应用正确性**
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    Property: For any template modifiers, the apply_modifiers output must
    contain the font style from the configuration.
    """
    # Arrange
    builder = PromptBuilder()
    modifiers = PromptModifiers(
        style_keywords=keywords,
        color_scheme=color,
        layout_hints=layout,
        font_style=font,
    )
    
    # Act
    result = builder.apply_modifiers(modifiers)
    
    # Assert: Font style must appear in the result
    assert font in result, (
        f"Font style '{font}' not found in apply_modifiers result: {result}"
    )


@settings(max_examples=100)
@given(
    keywords=style_keywords_list,
    color=color_scheme,
    layout=layout_hints,
    font=font_style,
    scene_desc=scene_description,
    marketing_text=mixed_text,
    language=st.sampled_from(["zh", "en"]),
    ratio=aspect_ratio,
)
def test_build_poster_prompt_with_modifiers_contains_all_params(
    keywords: list[str],
    color: str,
    layout: str,
    font: str,
    scene_desc: str,
    marketing_text: str,
    language: str,
    ratio: str,
) -> None:
    """
    **Feature: popgraph, Property 4: 模板参数应用正确性**
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    Property: For any poster generation request with template modifiers,
    the generated prompt must contain all template parameters (style keywords,
    color scheme, layout hints, and font style).
    """
    # Arrange
    builder = PromptBuilder()
    request = PosterGenerationRequest(
        scene_description=scene_desc,
        marketing_text=marketing_text,
        language=language,
        aspect_ratio=ratio,
        batch_size=1,
    )
    modifiers = PromptModifiers(
        style_keywords=keywords,
        color_scheme=color,
        layout_hints=layout,
        font_style=font,
    )
    
    # Act
    prompt = builder.build_poster_prompt(request, modifiers)
    
    # Assert: All template parameters must appear in the final prompt
    for keyword in keywords:
        assert keyword in prompt, (
            f"Style keyword '{keyword}' not found in final prompt: {prompt}"
        )
    
    assert color in prompt, (
        f"Color scheme '{color}' not found in final prompt: {prompt}"
    )
    
    assert layout in prompt, (
        f"Layout hints '{layout}' not found in final prompt: {prompt}"
    )
    
    assert font in prompt, (
        f"Font style '{font}' not found in final prompt: {prompt}"
    )


# ============================================================================
# Property 5: 模板与用户输入组合完整性
# **Feature: popgraph, Property 5: 模板与用户输入组合完整性**
# **Validates: Requirements 3.4**
#
# For any poster generation request with a template, the final prompt SHALL
# contain both the template's prompt modifiers AND the user-provided scene
# description and marketing text.
# ============================================================================


@settings(max_examples=100)
@given(
    keywords=style_keywords_list,
    color=color_scheme,
    layout=layout_hints,
    font=font_style,
    scene_desc=scene_description,
    marketing_text=mixed_text,
    language=st.sampled_from(["zh", "en"]),
    ratio=aspect_ratio,
    batch=batch_size,
)
def test_template_and_user_input_both_present_in_prompt(
    keywords: list[str],
    color: str,
    layout: str,
    font: str,
    scene_desc: str,
    marketing_text: str,
    language: str,
    ratio: str,
    batch: int,
) -> None:
    """
    **Feature: popgraph, Property 5: 模板与用户输入组合完整性**
    **Validates: Requirements 3.4**
    
    Property: For any poster generation request with a template, the final
    prompt must contain BOTH the template's prompt modifiers (style keywords,
    color scheme, layout hints, font style) AND the user-provided inputs
    (scene description and marketing text).
    """
    # Arrange
    builder = PromptBuilder()
    request = PosterGenerationRequest(
        scene_description=scene_desc,
        marketing_text=marketing_text,
        language=language,
        aspect_ratio=ratio,
        batch_size=batch,
    )
    modifiers = PromptModifiers(
        style_keywords=keywords,
        color_scheme=color,
        layout_hints=layout,
        font_style=font,
    )
    
    # Act
    prompt = builder.build_poster_prompt(request, modifiers)
    
    # Assert Part 1: User-provided scene description must be in the prompt
    assert scene_desc in prompt, (
        f"User scene description '{scene_desc}' not found in final prompt: {prompt}"
    )
    
    # Assert Part 2: User-provided marketing text must be in the prompt
    assert marketing_text in prompt, (
        f"User marketing text '{marketing_text}' not found in final prompt: {prompt}"
    )
    
    # Assert Part 3: All template style keywords must be in the prompt
    for keyword in keywords:
        assert keyword in prompt, (
            f"Template style keyword '{keyword}' not found in final prompt: {prompt}"
        )
    
    # Assert Part 4: Template color scheme must be in the prompt
    assert color in prompt, (
        f"Template color scheme '{color}' not found in final prompt: {prompt}"
    )
    
    # Assert Part 5: Template layout hints must be in the prompt
    assert layout in prompt, (
        f"Template layout hints '{layout}' not found in final prompt: {prompt}"
    )
    
    # Assert Part 6: Template font style must be in the prompt
    assert font in prompt, (
        f"Template font style '{font}' not found in final prompt: {prompt}"
    )
