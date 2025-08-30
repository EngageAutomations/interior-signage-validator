"""Font SVG Builder module for converting text to SVG outlines in millimeters."""

import os
import re
from pathlib import Path
from typing import Optional
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
import matplotlib.font_manager as fm


def slugify(value: str) -> str:
    """Convert a string to a filesystem-safe slug.
    
    Lowercases the string, replaces non-alphanumeric characters with underscores,
    and trims leading/trailing underscores.
    
    Args:
        value: The string to slugify
        
    Returns:
        A slugified string safe for use in filenames
    """
    # Convert to lowercase and replace non-alphanumeric with underscores
    slug = re.sub(r'[^a-z0-9]+', '_', value.lower())
    # Remove leading and trailing underscores
    return slug.strip('_')


def _find_font_file(font_name: str) -> str:
    """Find a TrueType font file by family name.
    
    Args:
        font_name: The font family name to search for
        
    Returns:
        Path to the font file, or default sans-serif if not found
    """
    try:
        # Try to find the specified font
        font_path = fm.findfont(fm.FontProperties(family=font_name))
        
        # Check if we got a valid font file (not the default fallback)
        if font_path and os.path.exists(font_path):
            # Verify it's actually the requested font by checking if the name matches
            try:
                test_font = TTFont(font_path)
                font_family = test_font['name'].getDebugName(1)  # Family name
                test_font.close()
                
                # If the family name contains our requested font, use it
                if font_name.lower() in font_family.lower():
                    return font_path
            except Exception:
                pass
    except Exception:
        pass
    
    # Fallback to default sans-serif
    return fm.findfont(fm.FontProperties(family='sans-serif'))


def build_text_svg(text: str, font_name: str) -> str:
    """Build an SVG string for the given text using the specified font.
    
    Args:
        text: The text to convert to SVG
        font_name: The font family name to use
        
    Returns:
        Complete SVG string with text rendered as paths in millimeter units
    """
    if not text.strip():
        return '<svg width="0mm" height="0mm" xmlns="http://www.w3.org/2000/svg"></svg>'
    
    # Find and load the font
    font_path = _find_font_file(font_name)
    font = TTFont(font_path)
    
    try:
        # Get font metrics
        units_per_em = font['head'].unitsPerEm
        ascender = font['hhea'].ascender
        descender = font['hhea'].descender
        
        # Calculate scaling factor: 72pt = 25.4mm, so mm_per_unit = 25.4 / units_per_em
        mm_per_unit = 25.4 / units_per_em
        
        # Get character map
        cmap = font.getBestCmap()
        glyf = font['glyf']
        hmtx = font['hmtx']
        
        # Build SVG paths for each character
        paths = []
        current_x = 0.0
        
        for char in text:
            char_code = ord(char)
            
            # Skip characters not in the font
            if char_code not in cmap:
                continue
                
            glyph_name = cmap[char_code]
            
            # Get glyph metrics
            advance_width, left_side_bearing = hmtx[glyph_name]
            
            # Create SVG path pen
            svg_pen = SVGPathPen(glyf.glyphSet)
            
            # Create transform: flip Y-axis, scale to mm, translate to position
            # Y-flip: multiply Y by -1
            # Scale: multiply by mm_per_unit
            # Translate: move to current X position, baseline at Y=0
            transform = Transform(
                xx=mm_per_unit,      # Scale X
                xy=0,
                yx=0,
                yy=-mm_per_unit,     # Scale and flip Y
                dx=current_x * mm_per_unit,  # Translate X
                dy=0                 # Baseline at Y=0
            )
            
            # Apply transform and draw glyph
            transform_pen = TransformPen(svg_pen, transform)
            glyf.glyphSet[glyph_name].draw(transform_pen)
            
            # Get the SVG path data
            path_data = svg_pen.getCommands()
            
            if path_data.strip():
                paths.append(f'<path d="{path_data}" fill="black" stroke="none"/>')
            
            # Advance to next character position
            current_x += advance_width
        
        # Calculate total dimensions in mm
        total_width_mm = current_x * mm_per_unit
        total_height_mm = (ascender - descender) * mm_per_unit
        
        # Assemble complete SVG
        svg_content = [
            f'<svg width="{total_width_mm:.2f}mm" height="{total_height_mm:.2f}mm" xmlns="http://www.w3.org/2000/svg">',
            '  <g>'
        ]
        
        for path in paths:
            svg_content.append(f'    {path}')
        
        svg_content.extend([
            '  </g>',
            '</svg>'
        ])
        
        return '\n'.join(svg_content)
        
    finally:
        font.close()


def build_font_svg(job_id: str, text: str, font_name: str) -> str:
    """Build and cache an SVG file for the given text and font.
    
    Creates the SVG file in the canonical location:
    interior_signage/{job_id}/fonts/{font_id}/{text_slug}.svg
    
    Args:
        job_id: Unique identifier for the job
        text: The text to convert to SVG
        font_name: The font family name to use
        
    Returns:
        Relative path to the created SVG file
    """
    # Create slugified identifiers
    font_id = slugify(font_name)
    text_slug = slugify(text)
    
    # Build the canonical path
    svg_dir = Path(f"interior_signage/{job_id}/fonts/{font_id}")
    svg_file = svg_dir / f"{text_slug}.svg"
    
    # Check if file already exists (caching)
    if svg_file.exists():
        return str(svg_file)
    
    # Create directory if it doesn't exist
    svg_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate SVG content
    svg_content = build_text_svg(text, font_name)
    
    # Write to file
    with open(svg_file, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    return str(svg_file)


if __name__ == "__main__":
    # Basic usage demonstration
    print("Font SVG Builder Demo")
    print("====================")
    
    # Test slugify function
    test_text = "CEO Office - Main Entrance!"
    print(f"Original text: '{test_text}'")
    print(f"Slugified: '{slugify(test_text)}'")
    print()
    
    # Test SVG generation
    sample_job_id = "demo_job_001"
    sample_text = "CEO Office"
    sample_font = "Arial"
    
    print(f"Generating SVG for:")
    print(f"  Job ID: {sample_job_id}")
    print(f"  Text: '{sample_text}'")
    print(f"  Font: {sample_font}")
    
    try:
        svg_path = build_font_svg(sample_job_id, sample_text, sample_font)
        print(f"  SVG saved to: {svg_path}")
        
        # Show file size
        if os.path.exists(svg_path):
            file_size = os.path.getsize(svg_path)
            print(f"  File size: {file_size} bytes")
            
            # Show first few lines of the SVG
            with open(svg_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
                print(f"  First few lines:")
                for line in lines:
                    print(f"    {line.rstrip()}")
        
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\nDemo complete!")