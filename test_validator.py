"""Unit tests for the SignageValidator class."""

import pytest
from interior_signage.validator import SignageValidator, ValidationResult


class TestSignageValidator:
    """Test cases for SignageValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SignageValidator()
        self.valid_spec = {
            "text": "CEO Office",
            "font": "Arial",
            "plate": {
                "width_mm": "200",
                "height_mm": "80",
                "thickness_mm": "3"
            },
            "bevel_mm": "0.5",
            "material": "brushed_metal",
            "finish": "satin",
            "color": "silver",
            "stand": "none",
            "text_style": "raised"
        }
    
    def test_valid_specification(self):
        """Test validation of a completely valid specification."""
        result = self.validator.validate_and_normalize(self.valid_spec)
        
        assert result.ok is True
        assert result.design_spec is not None
        assert result.issues is None
        assert result.needs == []
        
        # Check normalized values
        spec = result.design_spec
        assert spec["text"] == "CEO Office"
        assert spec["font"] == "Arial"
        assert spec["plate"]["width_mm"] == 200.0
        assert spec["plate"]["height_mm"] == 80.0
        assert spec["plate"]["thickness_mm"] == 3.0
        assert spec["bevel_mm"] == 0.5
        assert "font_size_pt" in spec
        assert isinstance(spec["font_size_pt"], float)
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        # Missing text
        spec = self.valid_spec.copy()
        del spec["text"]
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Missing required field: text" in result.issues
        
        # Missing font
        spec = self.valid_spec.copy()
        del spec["font"]
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Missing required field: font" in result.issues
        
        # Missing plate
        spec = self.valid_spec.copy()
        del spec["plate"]
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Missing required field: plate" in result.issues
    
    def test_empty_required_fields(self):
        """Test validation with empty required fields."""
        # Empty text
        spec = self.valid_spec.copy()
        spec["text"] = ""
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Field 'text' cannot be empty" in result.issues
        
        # Whitespace-only text
        spec["text"] = "   "
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Field 'text' cannot be empty" in result.issues
    
    def test_plate_validation(self):
        """Test plate dimension validation."""
        spec = self.valid_spec.copy()
        
        # Missing plate dimensions
        spec["plate"] = {"width_mm": "200"}
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Missing plate dimension: height_mm" in result.issues
        assert "Missing plate dimension: thickness_mm" in result.issues
        
        # Invalid plate dimensions
        spec["plate"] = {
            "width_mm": "0",
            "height_mm": "-10",
            "thickness_mm": "abc"
        }
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Plate width_mm must be greater than 0" in result.issues
        assert "Plate height_mm must be greater than 0" in result.issues
        assert "Plate thickness_mm must be a valid number" in result.issues
    
    def test_thickness_constraint(self):
        """Test minimum thickness constraint."""
        spec = self.valid_spec.copy()
        spec["plate"]["thickness_mm"] = "1.5"  # Below minimum
        
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Thickness must be ≥ 2.0 mm" in result.issues
    
    def test_bevel_constraint(self):
        """Test bevel constraint (≤ half thickness)."""
        spec = self.valid_spec.copy()
        spec["plate"]["thickness_mm"] = "4"
        spec["bevel_mm"] = "2.5"  # Greater than half thickness (2.0)
        
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Bevel must be ≤ half the thickness" in result.issues
    
    def test_numeric_string_conversion(self):
        """Test conversion of numeric strings to floats."""
        spec = self.valid_spec.copy()
        spec["plate"] = {
            "width_mm": "200.5",
            "height_mm": "80.25",
            "thickness_mm": "3.75"
        }
        spec["bevel_mm"] = "1.25"
        
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is True
        
        plate = result.design_spec["plate"]
        assert plate["width_mm"] == 200.5
        assert plate["height_mm"] == 80.25
        assert plate["thickness_mm"] == 3.75
        assert result.design_spec["bevel_mm"] == 1.25
    
    def test_default_values(self):
        """Test application of default values for optional fields."""
        # Minimal spec with only required fields
        minimal_spec = {
            "text": "Test",
            "font": "Arial",
            "plate": {
                "width_mm": "100",
                "height_mm": "50",
                "thickness_mm": "3"
            }
        }
        
        result = self.validator.validate_and_normalize(minimal_spec)
        assert result.ok is True
        
        spec = result.design_spec
        assert spec["material"] == "brushed_metal"
        assert spec["finish"] == "satin"
        assert spec["color"] == "silver"
        assert spec["stand"] == "none"
        assert spec["text_style"] == "raised"
        assert spec["bevel_mm"] == 0.5
    
    def test_invalid_choices(self):
        """Test validation of choice fields with invalid values."""
        spec = self.valid_spec.copy()
        spec["material"] = "invalid_material"
        spec["finish"] = "invalid_finish"
        
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is True  # Invalid choices use defaults
        
        # Should use defaults for invalid choices
        assert result.design_spec["material"] == "brushed_metal"
        assert result.design_spec["finish"] == "satin"
    
    def test_long_text(self):
        """Test validation with overly long text."""
        spec = self.valid_spec.copy()
        spec["text"] = "A" * 101  # Exceeds 100 character limit
        
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is False
        assert "Text is too long (max 100 characters)" in result.issues
    
    def test_font_size_calculation(self):
        """Test that font size is calculated and reasonable."""
        result = self.validator.validate_and_normalize(self.valid_spec)
        assert result.ok is True
        
        font_size = result.design_spec["font_size_pt"]
        assert isinstance(font_size, float)
        assert font_size > 0
        assert font_size < 200  # Reasonable upper bound
    
    def test_small_plate_font_calculation(self):
        """Test font calculation with very small plate."""
        spec = self.valid_spec.copy()
        spec["plate"] = {
            "width_mm": "20",
            "height_mm": "10",
            "thickness_mm": "2"
        }
        
        result = self.validator.validate_and_normalize(spec)
        # Should either succeed with small font or fail gracefully
        if result.ok:
            assert result.design_spec["font_size_pt"] > 0
        else:
            assert "Font size calculation failed" in str(result.issues)
    
    def test_whitespace_handling(self):
        """Test proper handling of whitespace in inputs."""
        spec = self.valid_spec.copy()
        spec["text"] = "  CEO Office  "
        spec["font"] = "  Arial  "
        spec["material"] = "  brushed_metal  "
        
        result = self.validator.validate_and_normalize(spec)
        assert result.ok is True
        
        # Whitespace should be stripped
        assert result.design_spec["text"] == "CEO Office"
        assert result.design_spec["font"] == "Arial"
        assert result.design_spec["material"] == "brushed_metal"