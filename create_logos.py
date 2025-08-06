#!/usr/bin/env python3
"""
Create logo files for SwissKnife AI Scraper
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_logo(size, output_path):
    """Create a simple logo with the specified size"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    primary_color = (25, 118, 210)  # Material-UI primary blue
    secondary_color = (255, 255, 255)  # White
    
    # Draw a circle background
    margin = size // 10
    draw.ellipse([margin, margin, size - margin, size - margin], 
                 fill=primary_color, outline=None)
    
    # Draw "SK" text in the center
    try:
        # Try to use a system font
        font_size = size // 3
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "SK"
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    draw.text((x, y), text, fill=secondary_color, font=font)
    
    # Save the image
    img.save(output_path, 'PNG')
    print(f"Created logo: {output_path}")

def main():
    """Create all required logo files"""
    frontend_public = "frontend/public"
    
    # Ensure directory exists
    os.makedirs(frontend_public, exist_ok=True)
    
    # Create logos
    create_logo(192, os.path.join(frontend_public, "logo192.png"))
    create_logo(512, os.path.join(frontend_public, "logo512.png"))
    
    # Create favicon (16x16 and 32x32 versions)
    create_logo(32, os.path.join(frontend_public, "favicon-32x32.png"))
    create_logo(16, os.path.join(frontend_public, "favicon-16x16.png"))
    
    print("All logo files created successfully!")

if __name__ == "__main__":
    main()
