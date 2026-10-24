"""
Image validation utilities for ShopEase multimodal customer support.
Validates file size, deep byte content format via Pillow, and detects spoofed extensions.
"""

import io
from pathlib import Path
from PIL import Image

# Maximum allowed image upload size (5 MB)
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024

FORMAT_TO_MIME = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp"
}

EXTENSION_TO_FORMAT = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP"
}


class ImageValidationError(Exception):
    """Raised when an uploaded image fails size, format, or content verification."""
    pass


def validate_image(image_bytes: bytes, filename: str = "upload.png") -> str:
    """
    Validate uploaded image bytes:
    1. Enforces <= 5 MB size limit
    2. Inspects actual byte stream using Pillow (detects corrupt files and fake extensions)
    3. Confirms format is PNG, JPG/JPEG, or WEBP
    4. Ensures file extension matches internal content format

    Returns:
        str: MIME type (e.g., 'image/png', 'image/jpeg', 'image/webp')

    Raises:
        ImageValidationError: If validation fails
    """
    if not image_bytes or len(image_bytes) == 0:
        raise ImageValidationError(f"Image '{filename}' is empty (0 bytes).")

    size_bytes = len(image_bytes)
    if size_bytes > MAX_IMAGE_SIZE_BYTES:
        size_mb = size_bytes / (1024 * 1024)
        raise ImageValidationError(
            f"Image '{filename}' exceeds maximum allowed size of 5 MB ({size_mb:.2f} MB)."
        )

    # Validate extension
    ext = Path(filename).suffix.lower()
    if ext not in EXTENSION_TO_FORMAT:
        allowed_exts = ", ".join(EXTENSION_TO_FORMAT.keys())
        raise ImageValidationError(
            f"Invalid file extension '{ext}' for image '{filename}'. Supported extensions are: {allowed_exts}"
        )

    # Deep byte validation using Pillow
    try:
        byte_stream = io.BytesIO(image_bytes)
        with Image.open(byte_stream) as img:
            img_format = img.format
            # Verify file integrity without fully decoding raster pixels
            img.verify()
    except Exception as exc:
        raise ImageValidationError(
            f"Invalid or corrupted image content in '{filename}': {exc}"
        )

    if not img_format or img_format not in FORMAT_TO_MIME:
        raise ImageValidationError(
            f"Unsupported image format '{img_format}' in '{filename}'. Only PNG, JPG/JPEG, and WEBP are supported."
        )

    # Check for extension spoofing (e.g. text file or JPEG renamed as .png)
    expected_format = EXTENSION_TO_FORMAT[ext]
    if img_format != expected_format:
        raise ImageValidationError(
            f"Mismatched extension and content: '{filename}' has extension '{ext}' but internal format is '{img_format}'."
        )

    return FORMAT_TO_MIME[img_format]
