"""Unit tests for TemplateService.

This module tests the template service with specific examples
to verify that templates are loaded correctly and template
parameters are merged properly.

Requirements: 3.1, 3.2, 3.3, 3.4
"""

import sys
from pathlib import Path

import pytest

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.schemas import (
    HolidayType,
    PosterGenerationRequest,
    PromptModifiers,
    Template,
    TemplateCategory,
)
from app.services.template_service import (
    ALL_TEMPLATES,
    HOLIDAY_TEMPLATES,
    PREMIUM_TEMPLATES,
    PROMOTIONAL_TEMPLATES,
    TEMPLATE_BY_ID,
    TemplateService,
)


class TestTemplateLoading:
    """测试模板加载正确"""

    def test_all_templates_loaded(self) -> None:
        """测试所有模板都已加载"""
        assert len(ALL_TEMPLATES) == 9  # 3 promotional + 3 premium + 3 holiday
        assert len(PROMOTIONAL_TEMPLATES) == 3
        assert len(PREMIUM_TEMPLATES) == 3
        assert len(HOLIDAY_TEMPLATES) == 3

    def test_template_by_id_lookup(self) -> None:
        """测试通过ID查找模板"""
        assert len(TEMPLATE_BY_ID) == 9
        assert "promo-sale-01" in TEMPLATE_BY_ID
        assert "premium-minimal-01" in TEMPLATE_BY_ID
        assert "holiday-spring-01" in TEMPLATE_BY_ID

    def test_promotional_templates_have_correct_category(self) -> None:
        """测试促销类模板分类正确"""
        for template in PROMOTIONAL_TEMPLATES:
            assert template.category == TemplateCategory.PROMOTIONAL
            assert template.holiday_type is None

    def test_premium_templates_have_correct_category(self) -> None:
        """测试高级类模板分类正确"""
        for template in PREMIUM_TEMPLATES:
            assert template.category == TemplateCategory.PREMIUM
            assert template.holiday_type is None

    def test_holiday_templates_have_correct_category(self) -> None:
        """测试节日类模板分类正确"""
        for template in HOLIDAY_TEMPLATES:
            assert template.category == TemplateCategory.HOLIDAY
            assert template.holiday_type is not None

    def test_all_templates_have_required_fields(self) -> None:
        """测试所有模板都有必需字段"""
        for template in ALL_TEMPLATES:
            assert template.id is not None and len(template.id) > 0
            assert template.name is not None and len(template.name) > 0
            assert template.category is not None
            assert template.prompt_modifiers is not None
            assert template.preview_url is not None

    def test_all_templates_have_valid_prompt_modifiers(self) -> None:
        """测试所有模板的 prompt_modifiers 有效"""
        for template in ALL_TEMPLATES:
            modifiers = template.prompt_modifiers
            assert len(modifiers.style_keywords) > 0
            assert len(modifiers.color_scheme) > 0
            assert len(modifiers.layout_hints) > 0
            assert len(modifiers.font_style) > 0


class TestPromotionalTemplates:
    """测试促销类模板 - Requirements: 3.1"""

    def test_promotional_template_has_red_background(self) -> None:
        """测试促销模板包含红色背景"""
        promo_template = TEMPLATE_BY_ID["promo-sale-01"]
        color_scheme = promo_template.prompt_modifiers.color_scheme.lower()
        assert "red" in color_scheme

    def test_promotional_template_has_explosion_style(self) -> None:
        """测试促销模板包含爆炸贴纸风格"""
        promo_template = TEMPLATE_BY_ID["promo-sale-01"]
        style_keywords = " ".join(promo_template.prompt_modifiers.style_keywords).lower()
        assert "explosion" in style_keywords or "burst" in style_keywords

    def test_promotional_template_has_large_font(self) -> None:
        """测试促销模板包含大字号"""
        promo_template = TEMPLATE_BY_ID["promo-sale-01"]
        font_style = promo_template.prompt_modifiers.font_style.lower()
        assert "large" in font_style or "bold" in font_style


class TestPremiumTemplates:
    """测试高级类模板 - Requirements: 3.2"""

    def test_premium_minimal_has_whitespace(self) -> None:
        """测试极简模板包含留白"""
        premium_template = TEMPLATE_BY_ID["premium-minimal-01"]
        layout_hints = premium_template.prompt_modifiers.layout_hints.lower()
        color_scheme = premium_template.prompt_modifiers.color_scheme.lower()
        assert "whitespace" in layout_hints or "white space" in color_scheme or "negative space" in layout_hints

    def test_premium_studio_has_lighting(self) -> None:
        """测试影棚模板包含光效"""
        studio_template = TEMPLATE_BY_ID["premium-studio-02"]
        style_keywords = " ".join(studio_template.prompt_modifiers.style_keywords).lower()
        assert "lighting" in style_keywords or "studio" in style_keywords

    def test_premium_blackgold_has_correct_colors(self) -> None:
        """测试黑金模板包含黑金配色"""
        blackgold_template = TEMPLATE_BY_ID["premium-blackgold-03"]
        color_scheme = blackgold_template.prompt_modifiers.color_scheme.lower()
        assert "black" in color_scheme and "gold" in color_scheme


class TestHolidayTemplates:
    """测试节日类模板 - Requirements: 3.3"""

    def test_spring_festival_template(self) -> None:
        """测试春节模板包含正确的节日元素"""
        spring_template = TEMPLATE_BY_ID["holiday-spring-01"]
        assert spring_template.holiday_type == HolidayType.SPRING_FESTIVAL
        style_keywords = " ".join(spring_template.prompt_modifiers.style_keywords).lower()
        assert "chinese new year" in style_keywords or "spring festival" in style_keywords

    def test_valentines_template(self) -> None:
        """测试情人节模板包含正确的节日元素"""
        valentines_template = TEMPLATE_BY_ID["holiday-valentines-02"]
        assert valentines_template.holiday_type == HolidayType.VALENTINES
        style_keywords = " ".join(valentines_template.prompt_modifiers.style_keywords).lower()
        assert "valentine" in style_keywords or "romantic" in style_keywords

    def test_double_eleven_template(self) -> None:
        """测试双十一模板包含正确的节日元素"""
        double11_template = TEMPLATE_BY_ID["holiday-double11-03"]
        assert double11_template.holiday_type == HolidayType.DOUBLE_ELEVEN
        style_keywords = " ".join(double11_template.prompt_modifiers.style_keywords).lower()
        assert "double eleven" in style_keywords or "11.11" in style_keywords


class TestTemplateServiceListTemplates:
    """测试 TemplateService.list_templates 方法"""

    @pytest.mark.asyncio
    async def test_list_all_templates(self) -> None:
        """测试列出所有模板"""
        service = TemplateService()
        templates = await service.list_templates()
        assert len(templates) == 9

    @pytest.mark.asyncio
    async def test_list_promotional_templates(self) -> None:
        """测试按分类列出促销模板"""
        service = TemplateService()
        templates = await service.list_templates(category=TemplateCategory.PROMOTIONAL)
        assert len(templates) == 3
        for t in templates:
            assert t.category == TemplateCategory.PROMOTIONAL

    @pytest.mark.asyncio
    async def test_list_premium_templates(self) -> None:
        """测试按分类列出高级模板"""
        service = TemplateService()
        templates = await service.list_templates(category=TemplateCategory.PREMIUM)
        assert len(templates) == 3
        for t in templates:
            assert t.category == TemplateCategory.PREMIUM

    @pytest.mark.asyncio
    async def test_list_holiday_templates(self) -> None:
        """测试按分类列出节日模板"""
        service = TemplateService()
        templates = await service.list_templates(category=TemplateCategory.HOLIDAY)
        assert len(templates) == 3
        for t in templates:
            assert t.category == TemplateCategory.HOLIDAY


class TestTemplateServiceGetTemplate:
    """测试 TemplateService.get_template 方法"""

    @pytest.mark.asyncio
    async def test_get_existing_template(self) -> None:
        """测试获取存在的模板"""
        service = TemplateService()
        template = await service.get_template("promo-sale-01")
        assert template is not None
        assert template.id == "promo-sale-01"
        assert template.name == "限时特惠"

    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self) -> None:
        """测试获取不存在的模板返回 None"""
        service = TemplateService()
        template = await service.get_template("nonexistent-template")
        assert template is None


class TestTemplateServiceGetTemplatesByHoliday:
    """测试 TemplateService.get_templates_by_holiday 方法"""

    @pytest.mark.asyncio
    async def test_get_spring_festival_templates(self) -> None:
        """测试获取春节模板"""
        service = TemplateService()
        templates = await service.get_templates_by_holiday(HolidayType.SPRING_FESTIVAL)
        assert len(templates) == 1
        assert templates[0].holiday_type == HolidayType.SPRING_FESTIVAL

    @pytest.mark.asyncio
    async def test_get_valentines_templates(self) -> None:
        """测试获取情人节模板"""
        service = TemplateService()
        templates = await service.get_templates_by_holiday(HolidayType.VALENTINES)
        assert len(templates) == 1
        assert templates[0].holiday_type == HolidayType.VALENTINES

    @pytest.mark.asyncio
    async def test_get_double_eleven_templates(self) -> None:
        """测试获取双十一模板"""
        service = TemplateService()
        templates = await service.get_templates_by_holiday(HolidayType.DOUBLE_ELEVEN)
        assert len(templates) == 1
        assert templates[0].holiday_type == HolidayType.DOUBLE_ELEVEN



class TestTemplateServiceApplyTemplate:
    """测试 TemplateService.apply_template 方法 - Requirements: 3.4"""

    @pytest.mark.asyncio
    async def test_apply_template_combines_template_and_user_input(self) -> None:
        """测试应用模板时合并模板参数和用户输入"""
        service = TemplateService()
        user_input = PosterGenerationRequest(
            scene_description="美丽的海滩风景",
            marketing_text="夏日特惠",
            language="zh",
            template_id="promo-sale-01",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        prompt = await service.apply_template("promo-sale-01", user_input)
        
        # 验证用户输入出现在 prompt 中
        assert "美丽的海滩风景" in prompt
        assert "夏日特惠" in prompt
        
        # 验证模板参数出现在 prompt 中
        template = TEMPLATE_BY_ID["promo-sale-01"]
        assert template.prompt_modifiers.color_scheme in prompt or "red" in prompt.lower()

    @pytest.mark.asyncio
    async def test_apply_template_includes_style_keywords(self) -> None:
        """测试应用模板时包含风格关键词"""
        service = TemplateService()
        user_input = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="限时优惠",
            language="zh",
            template_id="promo-sale-01",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        prompt = await service.apply_template("promo-sale-01", user_input)
        
        # 验证至少一个风格关键词出现在 prompt 中
        template = TEMPLATE_BY_ID["promo-sale-01"]
        style_keywords_found = any(
            keyword.lower() in prompt.lower() 
            for keyword in template.prompt_modifiers.style_keywords
        )
        assert style_keywords_found

    @pytest.mark.asyncio
    async def test_apply_template_includes_color_scheme(self) -> None:
        """测试应用模板时包含配色方案"""
        service = TemplateService()
        user_input = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="限时优惠",
            language="zh",
            template_id="premium-blackgold-03",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        prompt = await service.apply_template("premium-blackgold-03", user_input)
        
        # 验证配色方案出现在 prompt 中
        template = TEMPLATE_BY_ID["premium-blackgold-03"]
        assert template.prompt_modifiers.color_scheme in prompt

    @pytest.mark.asyncio
    async def test_apply_template_includes_layout_hints(self) -> None:
        """测试应用模板时包含排版提示"""
        service = TemplateService()
        user_input = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="限时优惠",
            language="zh",
            template_id="premium-minimal-01",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        prompt = await service.apply_template("premium-minimal-01", user_input)
        
        # 验证排版提示出现在 prompt 中
        template = TEMPLATE_BY_ID["premium-minimal-01"]
        assert template.prompt_modifiers.layout_hints in prompt

    @pytest.mark.asyncio
    async def test_apply_template_includes_font_style(self) -> None:
        """测试应用模板时包含字体风格"""
        service = TemplateService()
        user_input = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="限时优惠",
            language="zh",
            template_id="holiday-spring-01",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        prompt = await service.apply_template("holiday-spring-01", user_input)
        
        # 验证字体风格出现在 prompt 中
        template = TEMPLATE_BY_ID["holiday-spring-01"]
        assert template.prompt_modifiers.font_style in prompt

    @pytest.mark.asyncio
    async def test_apply_template_with_english_text(self) -> None:
        """测试应用模板时支持英文文案"""
        service = TemplateService()
        user_input = PosterGenerationRequest(
            scene_description="Beautiful sunset beach",
            marketing_text="Summer Sale",
            language="en",
            template_id="promo-sale-01",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        prompt = await service.apply_template("promo-sale-01", user_input)
        
        # 验证英文用户输入出现在 prompt 中
        assert "Beautiful sunset beach" in prompt
        assert "Summer Sale" in prompt

    @pytest.mark.asyncio
    async def test_apply_nonexistent_template_raises_error(self) -> None:
        """测试应用不存在的模板抛出错误"""
        service = TemplateService()
        user_input = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="限时优惠",
            language="zh",
            template_id="nonexistent",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        with pytest.raises(ValueError, match="Template not found"):
            await service.apply_template("nonexistent", user_input)

    @pytest.mark.asyncio
    async def test_apply_holiday_template_includes_festival_elements(self) -> None:
        """测试应用节日模板时包含节日元素"""
        service = TemplateService()
        user_input = PosterGenerationRequest(
            scene_description="新年祝福",
            marketing_text="恭喜发财",
            language="zh",
            template_id="holiday-spring-01",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        prompt = await service.apply_template("holiday-spring-01", user_input)
        
        # 验证春节相关元素出现在 prompt 中
        template = TEMPLATE_BY_ID["holiday-spring-01"]
        style_keywords = " ".join(template.prompt_modifiers.style_keywords).lower()
        assert "chinese new year" in style_keywords or "spring festival" in style_keywords
        # 验证至少一个风格关键词出现在 prompt 中
        assert any(kw.lower() in prompt.lower() for kw in template.prompt_modifiers.style_keywords)
