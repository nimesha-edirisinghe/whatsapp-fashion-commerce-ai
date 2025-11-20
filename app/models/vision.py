"""Vision and clothing attribute models."""

from typing import Any

from pydantic import BaseModel, Field


class ClothingAttributes(BaseModel):
    """Extracted clothing attributes from image analysis."""
    garment_type: str
    colors: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    style_keywords: list[str] = Field(default_factory=list)


class NonClothingResult(BaseModel):
    """Result when image is not clothing."""
    is_clothing: bool = False
    reason: str


class ImageAnalysisResult(BaseModel):
    """Combined result type for image analysis."""
    is_clothing: bool = True
    garment_type: str | None = None
    colors: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    style_keywords: list[str] = Field(default_factory=list)
    reason: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImageAnalysisResult":
        """Create from dictionary response."""
        if data.get("is_clothing") is False:
            return cls(
                is_clothing=False,
                reason=data.get("reason", "Not a clothing image"),
            )
        return cls(
            is_clothing=True,
            garment_type=data.get("garment_type"),
            colors=data.get("colors", []),
            patterns=data.get("patterns", []),
            style_keywords=data.get("style_keywords", []),
        )
