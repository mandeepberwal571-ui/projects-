"""
Multimodal Demonstration Script for ShopEase RAG Pipeline.
Demonstrates end-to-end processing of customer support inquiries with images:
1. Error screenshot (ERR_PAY_402)
2. Damaged product photo (SmartBand X1 cracked display)
3. Order receipt (Order #SE-9843210)

Usage:
python scripts/demo_multimodal.py
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm.rag_chain import RAGChain

ASSETS_DIR = PROJECT_ROOT / "tests" / "assets"

TEST_CASES = [
    {
        "filename": "error_screenshot.png",
        "question": "Why did my payment fail and how do I fix it?",
        "focus": "Payment Error Code (ERR_PAY_402)"
    },
    {
        "filename": "damaged_product.jpg",
        "question": "My fitness band arrived broken like this out of the box. Can I get a replacement?",
        "focus": "Physical Damage (48-hr SLA)"
    },
    {
        "filename": "receipt.png",
        "question": "Can I return the SmartBand X1 on this receipt?",
        "focus": "Receipt / Return Window"
    }
]


def run_demo():
    print("\n" + "=" * 74)
    print("           ShopEase Multimodal Customer Support RAG Demo          ")
    print("=" * 74)

    if not ASSETS_DIR.exists():
        print(f"[ERROR] Assets directory not found at: {ASSETS_DIR}")
        print("Please run: python scripts/generate_test_images.py")
        sys.exit(1)

    chain = RAGChain()

    for idx, case in enumerate(TEST_CASES, 1):
        filename = case["filename"]
        img_path = ASSETS_DIR / filename
        question = case["question"]
        focus = case["focus"]

        if not img_path.exists():
            print(f"[ERROR] Image not found: {img_path.name}")
            continue

        print(f"\n[Case {idx}/3]: {filename} ({focus})")
        print(f"Customer Question: \"{question}\"")
        print("-" * 74)

        img_bytes = img_path.read_bytes()
        response = chain.answer(query=question, image=img_bytes, image_filename=filename)

        # Vision metadata
        vis = response.image_description or {}
        print(f"• Issue Type:       {vis.get('issue_type', 'n/a')}")
        print(f"• Extracted Text:   {vis.get('extracted_text', 'n/a')}")
        print(f"• Description:      {vis.get('description', 'n/a')}")
        print(f"• Rewritten Query:  \"{response.rewritten_query}\"")
        print("-" * 74)
        print(f"ShopEase Assistant Answer:\n{response.answer}\n")
        print("-" * 74)

        print("Sources Cited:")
        for s_idx, src in enumerate(response.sources, 1):
            print(f"  [{s_idx}] {src.file} (Page {src.page}) | Score: {src.score:.4f}")

        status = "ESCALATED TO HUMAN AGENT" if response.escalate else "RESOLVED (Normal)"
        print(f"\nConfidence: {response.confidence:.4f} | Status: [{status}]")
        print("=" * 74)


if __name__ == "__main__":
    run_demo()
