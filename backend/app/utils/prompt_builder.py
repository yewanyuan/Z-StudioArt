"""Prompt Builder for PopGraph poster generation.

This module handles the construction of prompts for the Z-Image-Turbo model,
supporting Chinese and English text embedding and template parameter merging.

Requirements: 1.1, 1.2, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4
"""

from typing import Literal, Optional

from app.models.schemas import (
    PosterGenerationRequest,
    PromptModifiers,
)


class PromptBuilder:
    """Builds prompts for Z-Image-Turbo model.
    
    Handles text placement injection for Chinese/English text and
    template parameter merging for commercial poster generation.
    """
    
    # Base prompt template for commercial advertising style
    BASE_PROMPT_TEMPLATE = (
        "commercial advertising poster, professional photography, "
        "high quality, studio lighting, product showcase"
    )
    
    # Text placement instructions by language
    TEXT_PLACEMENT_TEMPLATES = {
        "zh": '中文文字 "{text}" 清晰渲染，文字排版美观，避免遮挡主体',
        "en": 'English text "{text}" clearly rendered, beautiful typography, avoid obscuring main subject',
    }
    
    def build_poster_prompt(
        self,
        request: PosterGenerationRequest,
        modifiers: Optional[PromptModifiers] = None,
    ) -> str:
        """Build a complete prompt for poster generation.
        
        Args:
            request: The poster generation request containing scene description,
                    marketing text, and language settings.
            modifiers: Optional template modifiers to apply.
            
        Returns:
            A complete prompt string for the AI model.
            
        Requirements: 1.1, 1.2, 1.4, 1.5
        """
        # Start with scene description
        prompt_parts = [request.scene_description]
        
        # Add base commercial style
        prompt_parts.append(self.BASE_PROMPT_TEMPLATE)
        
        # Inject text placement with the marketing text
        text_prompt = self.inject_text_placement(
            "", 
            request.marketing_text, 
            request.language
        )
        prompt_parts.append(text_prompt)
        
        # Apply modifiers if provided
        if modifiers:
            modifier_prompt = self.apply_modifiers(modifiers)
            prompt_parts.append(modifier_prompt)
        
        # Combine all parts
        return ", ".join(filter(None, prompt_parts))
    
    def inject_text_placement(
        self,
        base_prompt: str,
        text: str,
        language: Literal["zh", "en"],
    ) -> str:
        """Inject text placement instructions into the prompt.
        
        Ensures the marketing text is embedded correctly for the AI model
        to render it without garbled characters or deformation.
        
        Args:
            base_prompt: The base prompt to extend (can be empty).
            text: The marketing text to embed.
            language: The language of the text ('zh' or 'en').
            
        Returns:
            The prompt with text placement instructions.
            
        Requirements: 1.1, 1.2, 1.4
        """
        # Get the appropriate template for the language
        template = self.TEXT_PLACEMENT_TEMPLATES.get(
            language, 
            self.TEXT_PLACEMENT_TEMPLATES["en"]
        )
        
        # Format the template with the actual text
        text_instruction = template.format(text=text)
        
        # Combine with base prompt if provided
        if base_prompt:
            return f"{base_prompt}, {text_instruction}"
        return text_instruction
    
    def apply_modifiers(self, modifiers: PromptModifiers) -> str:
        """Apply template modifiers to generate prompt additions.
        
        Merges style keywords, color scheme, layout hints, and font style
        into a cohesive prompt segment.
        
        Args:
            modifiers: The prompt modifiers from a template.
            
        Returns:
            A prompt segment containing all modifier parameters.
            
        Requirements: 3.1, 3.2, 3.3, 3.4
        """
        parts = []
        
        # Add style keywords
        if modifiers.style_keywords:
            parts.append(", ".join(modifiers.style_keywords))
        
        # Add color scheme
        if modifiers.color_scheme:
            parts.append(f"color scheme: {modifiers.color_scheme}")
        
        # Add layout hints
        if modifiers.layout_hints:
            parts.append(f"layout: {modifiers.layout_hints}")
        
        # Add font style
        if modifiers.font_style:
            parts.append(f"font style: {modifiers.font_style}")
        
        return ", ".join(parts)
    
    def build_scene_fusion_prompt(
        self,
        scene: str,
        product_description: str,
    ) -> str:
        """Build a prompt for scene fusion.
        
        Creates a prompt that describes the target scene while maintaining
        the product's appearance.
        
        Args:
            scene: The target scene description.
            product_description: Description of the product to preserve.
            
        Returns:
            A prompt for scene fusion generation.
        """
        return (
            f"{scene}, featuring {product_description}, "
            "seamless integration, consistent lighting, "
            "matching perspective, professional product photography"
        )
