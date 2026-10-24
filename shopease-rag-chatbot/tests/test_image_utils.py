"""
Unit tests for image_utils.py.
Validates file size limits, deep byte content validation, and spoofed extension rejection.
Offline unit tests: requires no external network or API keys.
"""

import io
import pytest
from PIL import Image

from src.llm.image_utils import ImageValidationError, validate_image


def _create_in_memory_image(format_name: str) -> bytes:
    """Helper to generate in-memory image bytes."""
    img = Image.new("RGB", (100, 100), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    return buf.getvalue()


def test_valid_png_accepted():
    """Verify legitimate PNG bytes with .png extension are accepted."""
    data = _create_in_memory_image("PNG")
    mime = validate_image(data, "screenshot.png")
    assert mime == "image/png"


def test_valid_jpeg_accepted():
    """Verify legitimate JPEG bytes with .jpg and .jpeg extension are accepted."""
    data = _create_in_memory_image("JPEG")
    assert validate_image(data, "photo.jpg") == "image/jpeg"
    assert validate_image(data, "photo.jpeg") == "image/jpeg"


def test_valid_webp_accepted():
    """Verify legitimate WEBP bytes with .webp extension are accepted."""
    data = _create_in_memory_image("WEBP")
    mime = validate_image(data, "image.webp")
    assert mime == "image/webp"


def test_oversized_image_rejected():
    """Verify image larger than 5 MB is rejected."""
    # 5.1 MB of dummy data
    large_data = b"x" * (5 * 1024 * 1024 + 1024)
    with pytest.raises(ImageValidationError, match="exceeds maximum allowed size"):
        validate_image(large_data, "large.png")


def test_wrong_format_rejected():
    """Verify unsupported image formats like GIF or BMP are rejected."""
    gif_data = _create_in_memory_image("GIF")
    with pytest.raises(ImageValidationError, match="Invalid file extension"):
        validate_image(gif_data, "animation.gif")

    # If named .png but contains GIF bytes:
    with pytest.raises(ImageValidationError, match="Unsupported image format"):
        validate_image(gif_data, "fake.png")


def test_fake_extension_rejected():
    """Verify text file renamed to .png is rejected by deep byte inspection."""
    text_content = b"This is just plain text, not a real PNG image file."
    with pytest.raises(ImageValidationError, match="Invalid or corrupted image content"):
        validate_image(text_content, "sneaky_malware.png")


def test_mismatched_extension_and_content_rejected():
    """Verify JPEG file renamed to .png is rejected."""
    jpeg_data = _create_in_memory_image("JPEG")
    with pytest.raises(ImageValidationError, match="Mismatched extension and content"):
        validate_image(jpeg_data, "actually_jpeg.png")


def test_corrupted_bytes_rejected():
    """Verify corrupted header bytes are rejected."""
    corrupted = b"\x89PNG\r\n\x1a\n" + b"garbage_data_here" * 20
    with pytest.raises(ImageValidationError, match="Invalid or corrupted image content"):
        validate_image(corrupted, "corrupt.png")


def test_empty_image_rejected():
    """Verify empty byte string is rejected."""
    with pytest.raises(ImageValidationError, match="empty"):
        validate_image(b"", "empty.png")
