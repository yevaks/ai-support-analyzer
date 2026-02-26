"""CLI entry point for the AI Support Analyzer tool."""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _require_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit(
            "Error: GEMINI_API_KEY is not set.\n"
            "Add it to your .env file or export it as an environment variable."
        )
    return key


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------


def cmd_generate(args: argparse.Namespace) -> None:
    from src.llm import generate_dialogs
    from src.storage import save_json

    api_key = _require_api_key()
    dialogs = generate_dialogs(
        api_key=api_key,
        model=args.model,
        n=args.n,
        seed=args.seed,
    )
    save_json([d.model_dump() for d in dialogs], args.out)


def cmd_analyze(args: argparse.Namespace) -> None:
    from src.llm import analyze_dialogs
    from src.storage import load_json, save_json

    api_key = _require_api_key()
    dialogs = load_json(args.input)
    results = analyze_dialogs(
        api_key=api_key,
        model=args.model,
        dialogs=dialogs,
        seed=args.seed,
    )
    save_json([r.model_dump() for r in results], args.out)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Customer support dialog generator and analyzer powered by Gemini.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- generate ---
    gen = sub.add_parser("generate", help="Generate customer support dialogs.")
    gen.add_argument("--n", type=int, default=5, help="Number of dialogs to generate (default: 5).")
    gen.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42).")
    gen.add_argument(
        "--model",
        default="gemini-2.0-flash-lite",
        help="Gemini model name (default: gemini-2.0-flash-lite).",
    )
    gen.add_argument("--out", default="dataset.json", help="Output file path (default: dataset.json).")

    # --- analyze ---
    ana = sub.add_parser("analyze", help="Analyze a generated dialog dataset.")
    ana.add_argument("--input", default="dataset.json", help="Path to dataset JSON (default: dataset.json).")
    ana.add_argument("--seed", type=int, default=42, help="Seed used during generation (for traceability).")
    ana.add_argument(
        "--model",
        default="gemini-2.0-flash-lite",
        help="Gemini model name (default: gemini-2.0-flash-lite).",
    )
    ana.add_argument("--out", default="results.json", help="Output file path (default: results.json).")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
