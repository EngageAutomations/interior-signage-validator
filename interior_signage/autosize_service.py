"""FastAPI service for interior signage validation and font sizing."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
from .validator import SignageValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Interior Signage Validator",
    description="Validates and normalizes interior signage design specifications with automatic font size calculation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Pydantic models for request/response
class PlateRequest(BaseModel):
    """Plate dimensions request model."""
    width_mm: str = Field(..., description="Plate width in millimeters")
    height_mm: str = Field(..., description="Plate height in millimeters")
    thickness_mm: str = Field(..., description="Plate thickness in millimeters")

class SignageRequest(BaseModel):
    """Signage specification request model."""
    text: str = Field(..., description="Text to be displayed on the sign")
    font: str = Field(..., description="Font family name")
    plate: PlateRequest = Field(..., description="Plate dimensions")
    bevel_mm: Optional[str] = Field(None, description="Bevel size in millimeters")
    material: Optional[str] = Field(None, description="Plate material")
    finish: Optional[str] = Field(None, description="Surface finish")
    color: Optional[str] = Field(None, description="Plate color")
    stand: Optional[str] = Field(None, description="Stand type")
    text_style: Optional[str] = Field(None, description="Text style")

class ValidationResponse(BaseModel):
    """Validation response model."""
    ok: bool = Field(..., description="Whether validation was successful")
    design_spec: Optional[Dict[str, Any]] = Field(None, description="Normalized design specification")
    issues: Optional[List[str]] = Field(None, description="Validation issues if any")
    needs: Optional[List[str]] = Field(None, description="Additional requirements")

# Initialize validator
validator = SignageValidator()

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Interior Signage Validator",
        "version": "1.0.0",
        "description": "Validates and normalizes interior signage design specifications",
        "endpoints": {
            "/validate": "POST - Validate signage specification",
            "/health": "GET - Health check",
            "/docs": "GET - Interactive API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "interior-signage-validator"}

@app.post("/validate", response_model=ValidationResponse)
async def validate_signage(request: SignageRequest):
    """Validate and normalize a signage design specification.
    
    This endpoint accepts a signage specification and returns either:
    - A normalized specification with calculated font size (if valid)
    - A list of validation issues (if invalid)
    
    The validator enforces constraints such as:
    - Minimum thickness of 2mm
    - Bevel ≤ half the thickness
    - Text fits within plate dimensions with 5mm margins
    """
    try:
        # Convert Pydantic model to dict for validator
        spec_dict = {
            "text": request.text,
            "font": request.font,
            "plate": {
                "width_mm": request.plate.width_mm,
                "height_mm": request.plate.height_mm,
                "thickness_mm": request.plate.thickness_mm
            }
        }
        
        # Add optional fields if provided
        if request.bevel_mm is not None:
            spec_dict["bevel_mm"] = request.bevel_mm
        if request.material is not None:
            spec_dict["material"] = request.material
        if request.finish is not None:
            spec_dict["finish"] = request.finish
        if request.color is not None:
            spec_dict["color"] = request.color
        if request.stand is not None:
            spec_dict["stand"] = request.stand
        if request.text_style is not None:
            spec_dict["text_style"] = request.text_style
        
        # Validate the specification
        result = validator.validate_and_normalize(spec_dict)
        
        # Log the validation attempt
        logger.info(f"Validation request: ok={result.ok}, text='{request.text[:20]}...'")
        
        return ValidationResponse(
            ok=result.ok,
            design_spec=result.design_spec,
            issues=result.issues,
            needs=result.needs
        )
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal validation error: {str(e)}"
        )

# Error handlers
@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors."""
    return {
        "ok": False,
        "issues": ["Invalid request format. Please check the API documentation."],
        "detail": str(exc)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)