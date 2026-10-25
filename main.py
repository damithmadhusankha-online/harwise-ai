"""Harwise CLI. Run:  python main.py"""
import argparse

from agent.loop import HarwiseAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="Harwise: farm decision assistant (local LLM)")
    parser.add_argument("--model", default="qwen2.5:7b", help="Ollama model name")
    args = parser.parse_args()

    agent = HarwiseAgent(model=args.model)
    print(f"Harwise ready (model: {args.model}). Type 'quit' to exit, 'reset' to clear history.\n")

    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if text.lower() in {"quit", "exit"}:
            print("Bye.")
            break
        if text.lower() == "reset":
            agent.memory.clear()
            print("History cleared.\n")
            continue
        print("\nHarwise:", agent.ask(text), "\n")


if __name__ == "__main__":
    main()
