import sys, ast
from PIL import Image

def png_to_rgb666(input_file, output_file=None, background=(255, 255, 255)):
    """Convert PNG to RGB666 with transparent pixels replaced by specified background.
    
    Args:
        input_file: Path to PNG file
        output_file: Optional output file path
        background: RGB tuple for transparent areas (default white)
    Returns:
        bytes: RGB666 image data (3 bytes per pixel)
    """
    img = Image.open(input_file)
    
    # Convert to RGBA to handle transparency
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    width, height = img.size
    rgb666_data = bytearray()
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = img.getpixel((x, y))
            
            # Replace transparent pixels with background color
            if a < 255:
                r, g, b = background
            
            # Convert to RGB666 (effectively RGB888)
            rgb666_data.append(r)
            rgb666_data.append(g)
            rgb666_data.append(b)
    
    if output_file:
        with open(output_file, 'wb') as f:
            f.write(rgb666_data)
    
    return bytes(rgb666_data)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: png_to_rgb666.py input.png output.rgb666 [background]")
        print("Example: png_to_rgb666.py icon.png icon.rgb666 (255,255,255)")
        sys.exit(1)

    input_png = sys.argv[1]
    output_file = sys.argv[2]
    background = (255, 255, 255)  # Default white

    if len(sys.argv) > 3:
        try:
            # Safely evaluate the tuple string
            background = ast.literal_eval(sys.argv[3])
            if not (isinstance(background, tuple) and len(background) == 3):
                raise ValueError
        except (ValueError, SyntaxError):
            print("Error: Background must be in (R,G,B) format")
            sys.exit(1)

    print(f"Converting {input_png} to {output_file}")
    print(f"Transparent background will be: RGB{background}")
    png_to_rgb666(input_png, output_file, background)
    print("Conversion complete!")