"""Template Service for PopGraph.

This module manages preset commercial templates for poster generation,
including promotional, premium, and holiday templates.

Requirements: 3.1, 3.2, 3.3, 3.4
"""

from typing import Optional

from app.models.schemas import (
    HolidayType,
    PosterGenerationRequest,
    PromptModifiers,
    Template,
    TemplateCategory,
)
from app.utils.prompt_builder import PromptBuilder


# ============================================================================
# Preset Templates Data
# ============================================================================

# Promotional templates (促销类模板)
# Requirements: 3.1 - 红色背景、爆炸贴纸风格、大字号
PROMOTIONAL_TEMPLATES: list[Template] = [
    Template(
        id="promo-sale-01",
        name="限时特惠",
        category=TemplateCategory.PROMOTIONAL,
        holiday_type=None,
        prompt_modifiers=PromptModifiers(
            style_keywords=[
                "explosion sticker style",
                "bold promotional design",
                "eye-catching sale banner",
                "dynamic burst effect",
            ],
            color_scheme="vibrant red background with yellow accents",
            layout_hints="large centered text, starburst decorations, price tag emphasis",
            font_style="extra bold, large font size, impact style",
        ),
        preview_url="/templates/previews/promo-sale-01.jpg",
    ),
    Template(
        id="promo-flash-02",
        name="闪购秒杀",
        category=TemplateCategory.PROMOTIONAL,
        holiday_type=None,
        prompt_modifiers=PromptModifiers(
            style_keywords=[
                "flash sale design",
                "urgent promotional style",
                "lightning bolt effects",
                "countdown timer aesthetic",
            ],
            color_scheme="red and orange gradient with white highlights",
            layout_hints="diagonal text layout, urgency indicators, timer display",
            font_style="bold condensed, large numbers, attention-grabbing",
        ),
        preview_url="/templates/previews/promo-flash-02.jpg",
    ),
    Template(
        id="promo-discount-03",
        name="满减优惠",
        category=TemplateCategory.PROMOTIONAL,
        holiday_type=None,
        prompt_modifiers=PromptModifiers(
            style_keywords=[
                "discount banner style",
                "savings promotion design",
                "coupon aesthetic",
                "value proposition layout",
            ],
            color_scheme="red primary with gold trim",
            layout_hints="tiered discount display, clear price comparison, badge elements",
            font_style="bold serif, prominent numbers, hierarchical sizing",
        ),
        preview_url="/templates/previews/promo-discount-03.jpg",
    ),
]


# Premium templates (高级类模板)
# Requirements: 3.2 - 极简留白、影棚光效、黑金配色
PREMIUM_TEMPLATES: list[Template] = [
    Template(
        id="premium-minimal-01",
        name="极简奢华",
        category=TemplateCategory.PREMIUM,
        holiday_type=None,
        prompt_modifiers=PromptModifiers(
            style_keywords=[
                "minimalist luxury design",
                "elegant whitespace",
                "sophisticated aesthetic",
                "high-end brand style",
            ],
            color_scheme="black and gold with generous white space",
            layout_hints="centered composition, ample negative space, refined alignment",
            font_style="thin elegant serif, subtle gold accents, refined typography",
        ),
        preview_url="/templates/previews/premium-minimal-01.jpg",
    ),
    Template(
        id="premium-studio-02",
        name="影棚质感",
        category=TemplateCategory.PREMIUM,
        holiday_type=None,
        prompt_modifiers=PromptModifiers(
            style_keywords=[
                "studio lighting effect",
                "professional photography style",
                "dramatic shadows",
                "premium product showcase",
            ],
            color_scheme="deep black background with warm studio lighting",
            layout_hints="spotlight focus, gradient shadows, professional composition",
            font_style="modern sans-serif, clean lines, premium feel",
        ),
        preview_url="/templates/previews/premium-studio-02.jpg",
    ),
    Template(
        id="premium-blackgold-03",
        name="黑金尊享",
        category=TemplateCategory.PREMIUM,
        holiday_type=None,
        prompt_modifiers=PromptModifiers(
            style_keywords=[
                "black gold luxury",
                "VIP exclusive design",
                "opulent aesthetic",
                "premium membership style",
            ],
            color_scheme="matte black with metallic gold accents",
            layout_hints="symmetrical layout, gold border elements, luxury framing",
            font_style="elegant gold text, premium weight, luxurious typography",
        ),
        preview_url="/templates/previews/premium-blackgold-03.jpg",
    ),
]


# Holiday templates (节日类模板)
# Requirements: 3.3 - 春节、情人节、双十一
HOLIDAY_TEMPLATES: list[Template] = [
    Template(
        id="holiday-spring-01",
        name="春节喜庆",
        category=TemplateCategory.HOLIDAY,
        holiday_type=HolidayType.SPRING_FESTIVAL,
        prompt_modifiers=PromptModifiers(
            style_keywords=[
                "Chinese New Year celebration",
                "traditional festive design",
                "lucky red decorations",
                "spring festival elements",
            ],
            color_scheme="traditional Chinese red with gold, lantern motifs",
            layout_hints="symmetrical blessing layout, lantern decorations, fortune symbols",
            font_style="traditional Chinese calligraphy style, auspicious gold text",
        ),
        preview_url="/templates/previews/holiday-spring-01.jpg",
    ),
    Template(
        id="holiday-valentines-02",
        name="情人节浪漫",
        category=TemplateCategory.HOLIDAY,
        holiday_type=HolidayType.VALENTINES,
        prompt_modifiers=PromptModifiers(
            style_keywords=[
                "Valentine's Day romantic",
                "love theme design",
                "heart decorations",
                "romantic atmosphere",
            ],
            color_scheme="soft pink and red with rose gold accents",
            layout_hints="heart-shaped elements, romantic flourishes, couple-friendly layout",
            font_style="elegant script, romantic cursive, love-themed typography",
        ),
        preview_url="/templates/previews/holiday-valentines-02.jpg",
    ),
    Template(
        id="holiday-double11-03",
        name="双十一狂欢",
        category=TemplateCategory.HOLIDAY,
        holiday_type=HolidayType.DOUBLE_ELEVEN,
        prompt_modifiers=PromptModifiers(
            style_keywords=[
                "Double Eleven shopping festival",
                "11.11 sale celebration",
                "mega sale event",
                "shopping carnival design",
            ],
            color_scheme="vibrant red and orange with neon accents",
            layout_hints="dynamic diagonal layout, countdown elements, shopping cart icons",
            font_style="bold modern, large numbers, festival excitement",
        ),
        preview_url="/templates/previews/holiday-double11-03.jpg",
    ),
]

# All templates combined
ALL_TEMPLATES: list[Template] = (
    PROMOTIONAL_TEMPLATES + PREMIUM_TEMPLATES + HOLIDAY_TEMPLATES
)

# Template lookup by ID
TEMPLATE_BY_ID: dict[str, Template] = {t.id: t for t in ALL_TEMPLATES}



# ============================================================================
# Template Service Class
# ============================================================================

class TemplateService:
    """Service for managing and applying poster templates.
    
    Provides methods to list, retrieve, and apply templates to poster
    generation requests.
    
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    
    def __init__(self, prompt_builder: Optional[PromptBuilder] = None):
        """Initialize the template service.
        
        Args:
            prompt_builder: Optional PromptBuilder instance. If not provided,
                          a new instance will be created.
        """
        self._prompt_builder = prompt_builder or PromptBuilder()
    
    async def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
    ) -> list[Template]:
        """List available templates, optionally filtered by category.
        
        Args:
            category: Optional category to filter templates.
            
        Returns:
            List of templates matching the filter criteria.
            
        Requirements: 3.1, 3.2, 3.3
        """
        if category is None:
            return ALL_TEMPLATES.copy()
        
        return [t for t in ALL_TEMPLATES if t.category == category]
    
    async def get_template(self, template_id: str) -> Optional[Template]:
        """Get a specific template by ID.
        
        Args:
            template_id: The unique identifier of the template.
            
        Returns:
            The template if found, None otherwise.
        """
        return TEMPLATE_BY_ID.get(template_id)
    
    async def apply_template(
        self,
        template_id: str,
        user_input: PosterGenerationRequest,
    ) -> str:
        """Apply a template to user input and generate the final prompt.
        
        Combines the template's prompt modifiers with the user-provided
        scene description and marketing text to create a complete prompt.
        
        Args:
            template_id: The ID of the template to apply.
            user_input: The user's poster generation request.
            
        Returns:
            The complete prompt string combining template and user input.
            
        Raises:
            ValueError: If the template ID is not found.
            
        Requirements: 3.4
        """
        template = await self.get_template(template_id)
        if template is None:
            raise ValueError(f"Template not found: {template_id}")
        
        # Build the prompt with template modifiers
        return self._prompt_builder.build_poster_prompt(
            request=user_input,
            modifiers=template.prompt_modifiers,
        )
    
    async def get_templates_by_holiday(
        self,
        holiday_type: HolidayType,
    ) -> list[Template]:
        """Get templates for a specific holiday type.
        
        Args:
            holiday_type: The type of holiday to filter by.
            
        Returns:
            List of templates for the specified holiday.
            
        Requirements: 3.3
        """
        return [
            t for t in HOLIDAY_TEMPLATES
            if t.holiday_type == holiday_type
        ]
