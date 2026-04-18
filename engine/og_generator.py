import io

from PIL import Image, ImageDraw, ImageFont


def generate_og_image(title: str, scores: dict[str, int]) -> bytes:
    """
    Generate a 1200x630 OpenGraph image for an idea validation report.
    Returns bytes of the PNG image.
    """
    # 1. Setup Canvas
    width, height = 1200, 630
    # Background: AIdeator Dark (#0e0e0e)
    img = Image.new('RGB', (width, height), color='#0e0e0e')
    draw = ImageDraw.Draw(img)

    # 2. Load Fonts (Windows fallbacks)
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    try:
        title_font = ImageFont.truetype(font_path, 64)
        score_font = ImageFont.truetype(font_path, 48)
        label_font = ImageFont.truetype(font_path, 24)
        brand_font = ImageFont.truetype(font_path, 32)
    except Exception:
        title_font = ImageFont.load_default()  # type: ignore[assignment]
        score_font = ImageFont.load_default()  # type: ignore[assignment]
        label_font = ImageFont.load_default()  # type: ignore[assignment]
        brand_font = ImageFont.load_default()  # type: ignore[assignment]

    # 3. Draw Branding Accents
    # Gradient-like top border
    draw.rectangle([0, 0, width, 8], fill='#a7a5ff')
    
    # AIdeator Logo (Text for now)
    draw.text((60, 50), "AIDEATOR_OS", font=brand_font, fill='#a7a5ff')
    draw.text((60, 90), "INTELLIGENCE_SYNCHRONIZED", font=label_font, fill='#ffffff66')

    # 4. Draw Title
    # Wrap title if too long
    words = title.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        # Use simple heuristic for wrapping since ImageFont.getlength might not exist in old PIL
        if len(' '.join(current_line)) > 25:
            lines.append(' '.join(current_line))
            current_line = []
    if current_line:
        lines.append(' '.join(current_line))
    
    y_offset = 200
    for line in lines[:2]: # Limit to 2 lines
        draw.text((60, y_offset), line.upper(), font=title_font, fill='#ffffff')
        y_offset += 80

    # 5. Draw Scores (Horizontal layout)
    x_offset = 60
    for label, score in scores.items():
        # Draw Label
        draw.text((x_offset, 450), label.upper(), font=label_font, fill='#a7a5ff')
        # Draw Score
        draw.text((x_offset, 490), f"{score}%", font=score_font, fill='#ffffff')
        
        # Draw small bar
        draw.rectangle([x_offset, 560, x_offset + 200, 564], fill='#ffffff11')
        draw.rectangle([x_offset, 560, x_offset + (2 * score), 564], fill='#a7a5ff')
        
        x_offset += 300

    # 6. Save to Bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()
