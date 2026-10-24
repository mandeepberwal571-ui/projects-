"""
Interactive CLI Chat Demo for ShopEase RAG Pipeline.
Allows multi-turn conversational customer support inquiries with citations,
rewriting display, confidence scoring, and escalation alerts.

Usage:
python -m src.llm.chat_cli
"""

import sys
from typing import Dict, List
from src.llm.rag_chain import RAGChain


def run_chat():
    print("\n" + "=" * 65)
    print("      ShopEase Customer Support Assistant - Interactive CLI      ")
    print("=" * 65)
    print("Commands:")
    print("  'exit' or 'quit' : End the conversation")
    print("  'reset'          : Clear conversation memory")
    print("-" * 65)

    try:
        chain = RAGChain()
    except Exception as exc:
        print(f"\n[ERROR] Failed to initialize RAG Chain: {exc}")
        sys.exit(1)

    history: List[Dict[str, str]] = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for chatting with ShopEase Support. Have a great day!")
            break

        if user_input.lower() == "reset":
            history.clear()
            print("[Conversation memory cleared.]")
            continue

        print("\nThinking and searching documentation...")
        try:
            response = chain.answer(user_input, history=history)

            if response.rewritten_query != user_input:
                print(f"[Query Rewriter]: \"{response.rewritten_query}\"")

            print(f"\nShopEase Assistant:\n{response.answer}\n")

            # Print source citations
            if response.sources:
                print("-" * 65)
                print("Sources Cited:")
                for idx, src in enumerate(response.sources, 1):
                    print(f"  [{idx}] {src.file} (Page {src.page}) | Sim Score: {src.score:.4f}")

            # Confidence & Escalation indicator
            print("-" * 65)
            status_text = "NORMAL" if not response.escalate else "ESCALATED TO HUMAN AGENT"
            print(f"Confidence: {response.confidence:.4f} | Status: [{status_text}]")
            if response.escalate:
                print(">> [ALERT]: Low confidence or out-of-scope query. Transferring to human agent.")
            print("=" * 65)

            # Update history
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response.answer})

        except Exception as exc:
            print(f"\n[ERROR occurred during processing]: {exc}\n")


if __name__ == "__main__":
    run_chat()
