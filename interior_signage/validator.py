"""Core validation logic for interior signage specifications."""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt


@dataclass
class PlateSpec:
    """Plate specification with dimensions in millimeters."""
    width_mm: float
    height_mm: float
    thickness_mm: float


@dataclass
class ValidationResult:
    """Result of signage specification validation."""
    ok: bool
    design_spec: Optional[Dict[str, Any]] = None
    issues: Optional[List[str]] = None
    needs: Optional[List[str]] = None


class SignageValidator:
    """Validates and normalizes interior signage design specifications."""
    
    # Valid options for each field
    VALID_MATERIALS = {
        'brushed_metal', 'acrylic', 'wood', 'plastic', 'glass', 'aluminum'
    }
    VALID_FINISHES = {
        'satin', 'matte', 'gloss', 'brushed', 'polished', 'textured'
    }
    VALID_COLORS = {
        'silver', 'gold', 'black', 'white', 'bronze', 'copper', 'clear'
    }
    VALID_STANDS = {
        'none', 'desktop', 'wall_mount', 'floor_stand', 'magnetic'
    }
    VALID_TEXT_STYLES = {
        'raised', 'engraved', 'printed', 'etched', 'embossed'
    }
    
    # Default values
    DEFAULTS = {
        'material': 'brushed_metal',
        'finish': 'satin',
        'color': 'silver',
        'stand': 'none',
        'text_style': 'raised',
        'bevel_mm': 0.5
    }
    
    # Constraints
    MIN_THICKNESS_MM = 2.0
    MARGIN_MM = 5.0  # Margin around text
    
    def __init__(self):
        """Initialize the validator."""
        pass
    
    def validate_and_normalize(self, spec: Dict[str, Any]) -> ValidationResult:
        """Validate and normalize a signage specification.
        
        Args:
            spec: Raw specification dictionary
            
        Returns:
            ValidationResult with normalized spec or validation issues
        """
        issues = []
        normalized = {}
        
        # Validate required fields
        if not self._validate_required_fields(spec, issues):
            return ValidationResult(ok=False, issues=issues)
        
        # Normalize and validate text
        text = self._normalize_text(spec.get('text', ''), issues)
        if text is not None:
            normalized['text'] = text
        
        # Normalize and validate font
        font = self._normalize_font(spec.get('font', ''), issues)
        if font is not None:
            normalized['font'] = font
        
        # Normalize and validate plate dimensions
        plate = self._normalize_plate(spec.get('plate', {}), issues)
        if plate is not None:
            normalized['plate'] = plate
        
        # Normalize and validate bevel
        bevel = self._normalize_bevel(spec.get('bevel_mm'), plate, issues)
        if bevel is not None:
            normalized['bevel_mm'] = bevel
        
        # Normalize optional fields with defaults
        normalized['material'] = self._normalize_choice(
            spec.get('material'), self.VALID_MATERIALS, 
            self.DEFAULTS['material'], 'material', issues
        )
        normalized['finish'] = self._normalize_choice(
            spec.get('finish'), self.VALID_FINISHES,
            self.DEFAULTS['finish'], 'finish', issues
        )
        normalized['color'] = self._normalize_choice(
            spec.get('color'), self.VALID_COLORS,
            self.DEFAULTS['color'], 'color', issues
        )
        normalized['stand'] = self._normalize_choice(
            spec.get('stand'), self.VALID_STANDS,
            self.DEFAULTS['stand'], 'stand', issues
        )
        normalized['text_style'] = self._normalize_choice(
            spec.get('text_style'), self.VALID_TEXT_STYLES,
            self.DEFAULTS['text_style'], 'text_style', issues
        )
        
        # If we have validation issues, return them
        if issues:
            return ValidationResult(ok=False, issues=issues)
        
        # Calculate maximum font size
        try:
            font_size = self._calculate_max_font_size(
                normalized['text'], normalized['font'], normalized['plate']
            )
            normalized['font_size_pt'] = font_size
        except Exception as e:
            issues.append(f"Font size calculation failed: {str(e)}")
            return ValidationResult(ok=False, issues=issues)
        
        return ValidationResult(
            ok=True, 
            design_spec=normalized, 
            needs=[]
        )
    
    def _validate_required_fields(self, spec: Dict[str, Any], issues: List[str]) -> bool:
        """Validate that required fields are present and not empty."""
        required_fields = ['text', 'font', 'plate']
        
        for field in required_fields:
            if field not in spec:
                issues.append(f"Missing required field: {field}")
            elif not spec[field] or (isinstance(spec[field], str) and not spec[field].strip()):
                issues.append(f"Field '{field}' cannot be empty")
        
        return len(issues) == 0
    
    def _normalize_text(self, text: Any, issues: List[str]) -> Optional[str]:
        """Normalize and validate text field."""
        if not isinstance(text, str):
            issues.append("Text must be a string")
            return None
        
        text = text.strip()
        if not text:
            issues.append("Text cannot be empty")
            return None
        
        if len(text) > 100:  # Reasonable limit
            issues.append("Text is too long (max 100 characters)")
            return None
        
        return text
    
    def _normalize_font(self, font: Any, issues: List[str]) -> Optional[str]:
        """Normalize and validate font field."""
        if not isinstance(font, str):
            issues.append("Font must be a string")
            return None
        
        font = font.strip()
        if not font:
            issues.append("Font cannot be empty")
            return None
        
        # Basic font name validation
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', font):
            issues.append("Font name contains invalid characters")
            return None
        
        return font
    
    def _normalize_plate(self, plate: Any, issues: List[str]) -> Optional[Dict[str, float]]:
        """Normalize and validate plate dimensions."""
        if not isinstance(plate, dict):
            issues.append("Plate must be an object with width_mm, height_mm, and thickness_mm")
            return None
        
        required_dims = ['width_mm', 'height_mm', 'thickness_mm']
        normalized_plate = {}
        
        for dim in required_dims:
            if dim not in plate:
                issues.append(f"Missing plate dimension: {dim}")
                continue
            
            try:
                value = float(str(plate[dim]).strip())
                if value <= 0:
                    issues.append(f"Plate {dim} must be greater than 0")
                    continue
                normalized_plate[dim] = value
            except (ValueError, AttributeError):
                issues.append(f"Plate {dim} must be a valid number")
                continue
        
        if len(normalized_plate) != 3:
            return None
        
        # Validate thickness constraint
        if normalized_plate['thickness_mm'] < self.MIN_THICKNESS_MM:
            issues.append(f"Thickness must be ≥ {self.MIN_THICKNESS_MM} mm")
            return None
        
        return normalized_plate
    
    def _normalize_bevel(self, bevel: Any, plate: Optional[Dict[str, float]], 
                        issues: List[str]) -> Optional[float]:
        """Normalize and validate bevel dimension."""
        if bevel is None or bevel == '':
            return self.DEFAULTS['bevel_mm']
        
        try:
            bevel_value = float(str(bevel).strip())
            if bevel_value < 0:
                issues.append("Bevel cannot be negative")
                return None
            
            # Validate bevel constraint (≤ half thickness)
            if plate and bevel_value > plate['thickness_mm'] / 2:
                issues.append("Bevel must be ≤ half the thickness")
                return None
            
            return bevel_value
        except (ValueError, AttributeError):
            issues.append("Bevel must be a valid number")
            return None
    
    def _normalize_choice(self, value: Any, valid_choices: set, default: str, 
                         field_name: str, issues: List[str]) -> str:
        """Normalize and validate choice fields."""
        if value is None or value == '':
            return default
        
        if not isinstance(value, str):
            issues.append(f"{field_name} must be a string")
            return default
        
        value = value.strip().lower()
        if value not in valid_choices:
            issues.append(
                f"Invalid {field_name}: '{value}'. "
                f"Valid options: {', '.join(sorted(valid_choices))}"
            )
            return default
        
        return value
    
    def _calculate_max_font_size(self, text: str, font_name: str, 
                                plate: Dict[str, float]) -> float:
        """Calculate maximum font size that fits within plate dimensions.
        
        Args:
            text: Text to be displayed
            font_name: Font family name
            plate: Plate dimensions dictionary
            
        Returns:
            Maximum font size in points
        """
        # Available space (plate dimensions minus margins)
        available_width = plate['width_mm'] - (2 * self.MARGIN_MM)
        available_height = plate['height_mm'] - (2 * self.MARGIN_MM)
        
        if available_width <= 0 or available_height <= 0:
            raise ValueError("Plate too small for text with required margins")
        
        # Binary search for maximum font size
        min_size, max_size = 1.0, 200.0
        tolerance = 0.1
        
        while max_size - min_size > tolerance:
            test_size = (min_size + max_size) / 2
            
            try:
                # Create font properties
                font_props = FontProperties(family=font_name, size=test_size)
                
                # Create text path to get bounding box
                text_path = TextPath((0, 0), text, size=test_size, prop=font_props)
                bbox = text_path.get_extents()
                
                # Convert from points to mm (1 point = 0.352778 mm)
                text_width_mm = bbox.width * 0.352778
                text_height_mm = bbox.height * 0.352778
                
                # Check if text fits
                if text_width_mm <= available_width and text_height_mm <= available_height:
                    min_size = test_size
                else:
                    max_size = test_size
                    
            except Exception:
                # If font rendering fails, try a smaller size
                max_size = test_size
        
        return round(min_size, 1)