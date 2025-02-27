import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
import io
import os

def create_layout_preview():
    """Generate a preview image showing the application layout"""
    # Create an image with the dimensions of our window
    width = 780
    height = 580
    
    # Create the image
    img = Image.new('RGBA', (width, height), (26, 26, 46, 255))  # Dark blue background
    draw = ImageDraw.Draw(img)
    
    # Define colors
    header_color = (30, 30, 48, 255)
    sidebar_color = (37, 37, 56, 255)
    content_color = (30, 30, 48, 255)
    player_color = (30, 30, 48, 255)
    accent_color = (76, 201, 240, 255)
    
    # Define regions
    header_height = 60
    player_height = 100
    sidebar_width = 200
    
    # Draw header
    draw.rectangle([0, 0, width, header_height], fill=header_color)
    
    # Draw content area
    content_top = header_height
    content_bottom = height - player_height
    
    # Draw sidebar
    draw.rectangle([15, content_top + 10, sidebar_width + 5, content_bottom - 10], fill=sidebar_color)
    
    # Draw content
    draw.rectangle([sidebar_width + 15, content_top + 10, width - 15, content_bottom - 10], fill=content_color)
    
    # Draw player bar with accent border
    draw.rectangle([0, content_bottom, width, height], fill=player_color)
    draw.rectangle([0, content_bottom, width, content_bottom + 2], fill=accent_color)  # Accent border
    
    # Add some descriptive text
    try:
        # Try to get a font - this might fail if font is not available
        font = ImageFont.truetype("arial.ttf", 14)
        draw.text((width//2 - 100, 20), "AUDIO TO MIC PLAYER", fill=(255, 255, 255, 255), font=font)
        draw.text((sidebar_width//2 - 40, content_top + 20), "Settings", fill=(255, 255, 255, 255), font=font)
        draw.text((sidebar_width + 100, content_top + 20), "Audio Files", fill=(255, 255, 255, 255), font=font)
        draw.text((width//2 - 60, content_bottom + 20), "Player Controls", fill=(255, 255, 255, 255), font=font)
    except:
        # Fallback if font not available
        pass
    
    # Save the image
    output_path = os.path.join(os.path.dirname(__file__), "layout_preview.png")
    img.save(output_path)
    print(f"Layout preview saved to {output_path}")
    return output_path

if __name__ == "__main__":
    create_layout_preview()
