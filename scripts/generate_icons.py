"""
Icon Generator for DMLClean

Generates all required icon formats from logo.jpeg:
- Windows: .ico (multiple sizes)
- macOS: .icns
- Linux: .png (multiple sizes)

Usage:
    python scripts/generate_icons.py
"""

from pathlib import Path
from PIL import Image
import struct


def generate_ico(source: Path, output: Path) -> None:
    """
    Generate Windows .ico file with multiple sizes.
    
    Creates icon with sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
    """
    img = Image.open(source)
    
    # Icon sizes to generate
    sizes = [16, 32, 48, 64, 128, 256]
    
    ico_data = []
    
    # ICONDIR header (6 bytes)
    ico_data.append(struct.pack('<HHH', 0, 1, len(sizes)))
    
    for size in sizes:
        # Resize image
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Convert to RGBA for proper alpha handling
        if resized.mode != 'RGBA':
            resized = resized.convert('RGBA')
        
        # Create BMP data (XOR mask + AND mask)
        width, height = size, size
        
        # BMP header (40 bytes) + color data + alpha
        bmp_header = struct.pack('<IiiHHIIIIII', 
            40,  # Header size
            width,  # Width
            height * 2,  # Height (doubled for AND mask)
            1,  # Planes
            32,  # Bit count (RGBA)
            0,  # Compression (BI_RGB)
            0,  # Image size (can be 0 for BI_RGB)
            0,  # X pixels per meter
            0,  # Y pixels per meter
            0,  # Colors used
            0   # Important colors
        )
        
        # Get pixel data
        pixels = list(resized.getdata())
        
        # BMP stores bottom-to-top, so reverse rows
        bmp_data = bytearray()
        for y in range(height - 1, -1, -1):
            for x in range(width):
                pixel = pixels[y * width + x]
                # BGRA format (BMP stores as BGRA)
                bmp_data.extend([pixel[2], pixel[1], pixel[0], pixel[3]])
        
        # AND mask (1 bit per pixel, all 0s = fully opaque)
        and_mask_size = ((width + 31) // 32) * 4 * height
        and_mask = b'\x00' * and_mask_size
        
        icon_data = bmp_header + bytes(bmp_data) + and_mask
        
        # ICONDIRENTRY (16 bytes per icon)
        icon_entry = struct.pack('<BBBBHHII',
            width if width < 256 else 0,  # Width (0 = 256)
            height if height < 256 else 0,  # Height (0 = 256)
            0,  # Color count
            0,  # Reserved
            0,  # Color planes (0 or 1)
            32,  # Bits per pixel
            len(icon_data),  # Image size
            6 + 16 * len(ico_data)  # Image offset
        )
        ico_data.append(icon_entry)
        ico_data.append(icon_data)
    
    # Write ICO file
    with open(output, 'wb') as f:
        for data in ico_data:
            if isinstance(data, bytes):
                f.write(data)
            else:
                f.write(data)
    
    print(f"✓ Generated Windows icon: {output}")


def generate_icns(source: Path, output: Path) -> None:
    """
    Generate macOS .icns file with multiple sizes.
    
    Creates iconset with sizes: 16x16, 32x32, 64x64, 128x128, 256x256, 512x512, 1024x1024
    
    Uses pure Python implementation for cross-platform compatibility.
    """
    import io
    
    # macOS icon types and sizes
    icon_types = {
        b'ic07': (128, 128),   # 128x128
        b'ic08': (256, 256),   # 256x256
        b'ic09': (512, 512),   # 512x512
        b'ic10': (1024, 1024), # 1024x1024 (macOS 10.9+)
        b'ic11': (32, 32),     # 32x32 (macOS 10.9+)
        b'ic12': (64, 64),     # 64x64 (macOS 10.9+)
        b'ic13': (256, 256),   # 256x256@2x (macOS 10.9+)
        b'ic14': (512, 512),   # 512x512@2x (macOS 10.9+)
    }
    
    img = Image.open(source)
    icon_data = []
    
    for icon_type, (width, height) in icon_types.items():
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        if resized.mode != 'RGBA':
            resized = resized.convert('RGBA')
        
        # Save as PNG in memory
        png_buffer = io.BytesIO()
        resized.save(png_buffer, format='PNG')
        png_data = png_buffer.getvalue()
        
        # Icon structure: type (4) + size (4) + data
        icon_size = 8 + len(png_data)
        icon_entry = struct.pack('>4sI', icon_type, icon_size) + png_data
        icon_data.append(icon_entry)
    
    # Calculate total size
    total_size = 8  # Header
    for data in icon_data:
        total_size += len(data)
    
    # Write ICNS file
    with open(output, 'wb') as f:
        # ICNS header: magic (4) + size (4)
        f.write(struct.pack('>4sI', b'icns', total_size))
        
        # Write all icon entries
        for data in icon_data:
            f.write(data)
    
    print(f"✓ Generated macOS icon: {output}")


def generate_png(source: Path, output_dir: Path) -> None:
    """
    Generate Linux .png files in multiple sizes.
    
    Creates: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256, 512x512
    """
    img = Image.open(source)
    
    sizes = [16, 32, 48, 64, 128, 256, 512]
    
    for size in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        if resized.mode != 'RGBA':
            resized = resized.convert('RGBA')
        
        output_path = output_dir / f"dmlclean_{size}x{size}.png"
        resized.save(output_path, 'PNG')
        print(f"✓ Generated PNG icon: {output_path}")
    
    # Also create default size (256x256)
    default = img.resize((256, 256), Image.Resampling.LANCZOS)
    if default.mode != 'RGBA':
        default = default.convert('RGBA')
    default_output = output_dir / "dmlclean.png"
    default.save(default_output, 'PNG')
    print(f"✓ Generated default PNG icon: {default_output}")


def main():
    """Generate all icon formats."""
    # Paths
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets"
    
    # Find source image (prefer logo.jpeg, fallback to dmlclean.png)
    source_logo = assets_dir / "logo.jpeg"
    if not source_logo.exists():
        # Use existing dmlclean.png as source if logo.jpeg doesn't exist
        source_logo = assets_dir / "dmlclean.png"
        if not source_logo.exists():
            print(f"✗ Error: No source logo found in {assets_dir}")
            print("   Please add logo.jpeg or dmlclean.png to assets/")
            return 1
    
    print(f"Generating icons from: {source_logo}")
    print("-" * 50)
    
    # Generate Windows .ico
    ico_output = assets_dir / "dmlclean.ico"
    generate_ico(source_logo, ico_output)
    
    # Generate macOS .icns
    icns_output = assets_dir / "dmlclean.icns"
    generate_icns(source_logo, icns_output)
    
    # Generate Linux .png files
    generate_png(source_logo, assets_dir)
    
    print("-" * 50)
    print("✓ Icon generation complete!")
    print(f"  Windows: {ico_output}")
    print(f"  macOS:   {icns_output}")
    print(f"  Linux:   {assets_dir / 'dmlclean.png'}")
    
    return 0


if __name__ == "__main__":
    exit(main())
