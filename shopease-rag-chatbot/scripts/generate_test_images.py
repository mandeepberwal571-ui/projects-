"""
Generate 3 realistic synthetic test images for Phase 4 Multimodal RAG testing:
1. error_screenshot.png (Checkout failure with ERR_PAY_402)
2. damaged_product.jpg (Cracked display photo of SmartBand X1)
3. receipt.png (ShopEase order receipt with Order #SE-9843210)

Usage:
python scripts/generate_test_images.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "tests" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def create_error_screenshot():
    """Create a simulated mobile checkout payment error screen."""
    width, height = 640, 360
    img = Image.new("RGB", (width, height), color=(15, 23, 42))  # Dark slate
    draw = ImageDraw.Draw(img)

    # Red error banner
    draw.rectangle([(20, 30), (width - 20, 100)], fill=(220, 38, 38))
    draw.text((40, 50), "PAYMENT TRANSACTION FAILED", fill=(255, 255, 255))

    # Error code container
    draw.rectangle([(20, 120), (width - 20, 320)], fill=(30, 41, 59), outline=(71, 85, 105), width=2)
    draw.text((40, 140), "Error Code: ERR_PAY_402", fill=(239, 68, 68))
    draw.text((40, 180), "Reason: 3D Secure Verification Timeout (180s exceeded)", fill=(241, 245, 249))
    draw.text((40, 220), "Card: Visa ending in 4022 | Merchant: ShopEase E-Commerce", fill=(148, 163, 184))
    draw.text((40, 260), "Action: Retry purchase or select alternate payment method.", fill=(250, 204, 21))

    output_path = ASSETS_DIR / "error_screenshot.png"
    img.save(output_path, format="PNG")
    print(f"Created: {output_path.name} ({output_path.stat().st_size} bytes)")


def create_damaged_product_image():
    """Create a simulated photo of a physically damaged SmartBand X1."""
    width, height = 640, 360
    img = Image.new("RGB", (width, height), color=(241, 245, 249))  # Light background
    draw = ImageDraw.Draw(img)

    # Fitness band body
    draw.rectangle([(160, 100), (480, 260)], fill=(30, 41, 59))
    draw.rounded_rectangle([(240, 110), (400, 250)], radius=15, fill=(15, 23, 42), outline=(100, 116, 139), width=2)

    # Jagged crack lines across screen
    crack_points = [(260, 130), (290, 170), (320, 160), (350, 220), (380, 200)]
    draw.line(crack_points, fill=(239, 68, 68), width=3)
    draw.line([(290, 170), (270, 210)], fill=(239, 68, 68), width=2)
    draw.line([(320, 160), (360, 140)], fill=(239, 68, 68), width=2)

    # Damaged claim header badge
    draw.rectangle([(20, 20), (width - 20, 70)], fill=(185, 28, 28))
    draw.text((40, 35), "DAMAGED TRANSIT ITEM: ShopEase SmartBand X1", fill=(255, 255, 255))

    # Inspection details
    draw.text((40, 290), "Product: ShopEase SmartBand X1 (Model: SBX1-2026-BLK)", fill=(30, 41, 59))
    draw.text((40, 320), "Visible Defect: Fractured AMOLED screen upon package unboxing", fill=(185, 28, 28))

    output_path = ASSETS_DIR / "damaged_product.jpg"
    img.save(output_path, format="JPEG", quality=90)
    print(f"Created: {output_path.name} ({output_path.stat().st_size} bytes)")


def create_receipt_image():
    """Create a simulated customer order invoice receipt."""
    width, height = 500, 420
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Border
    draw.rectangle([(15, 15), (width - 15, height - 15)], outline=(203, 213, 225), width=2)

    # Header
    draw.rectangle([(25, 25), (width - 25, 75)], fill=(37, 99, 235))
    draw.text((40, 40), "SHOPEASE OFFICIAL ORDER RECEIPT", fill=(255, 255, 255))

    # Order details
    y = 95
    lines = [
        ("Order Number:", "#SE-9843210"),
        ("Order Date:", "October 14, 2026"),
        ("Customer ID:", "CUST-49102-US"),
        ("--------------------------------------------", ""),
        ("Item: ShopEase SmartBand X1", "$49.99"),
        ("Item: Silicone Sport Strap (Blue)", "$9.99"),
        ("Standard Shipping (3-5 Days):", "$4.99"),
        ("Estimated Sales Tax (GST/VAT):", "$5.20"),
        ("--------------------------------------------", ""),
        ("TOTAL CHARGED (Visa ****9211):", "$70.17"),
        ("Status:", "DELIVERED (Carrier: UPS Ground)")
    ]

    for label, val in lines:
        if not val:
            draw.text((40, y), label, fill=(148, 163, 184))
        else:
            draw.text((40, y), label, fill=(15, 23, 42))
            draw.text((320, y), val, fill=(15, 23, 42) if "TOTAL" not in label else (37, 99, 235))
        y += 26

    output_path = ASSETS_DIR / "receipt.png"
    img.save(output_path, format="PNG")
    print(f"Created: {output_path.name} ({output_path.stat().st_size} bytes)")


def main():
    print("Generating synthetic multimodal test images in:", ASSETS_DIR)
    create_error_screenshot()
    create_damaged_product_image()
    create_receipt_image()
    print("All 3 test images created successfully!\n")


if __name__ == "__main__":
    main()
