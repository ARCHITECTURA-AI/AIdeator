from engine.og_generator import generate_og_image


def test_generate_og_image_returns_bytes():
    title = "Test Business Idea"
    scores = {"Market": 80, "Moat": 60, "Viability": 90}
    
    img_bytes = generate_og_image(title, scores)
    
    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 0
    # Basic PNG header check
    assert img_bytes[:8] == b'\x89PNG\r\n\x1a\n'

def test_generate_og_image_long_title():
    title = (
        "This is a very long title that should definitely wrap across "
        "multiple lines in the generated image output"
    )
    scores = {"Test": 100}
    
    img_bytes = generate_og_image(title, scores)
    assert len(img_bytes) > 0

def test_generate_og_image_empty_scores():
    img_bytes = generate_og_image("No scores", {})
    assert len(img_bytes) > 0
