# AI Support Analyzer

A production-ready CLI tool for **generating** and **analyzing** customer support dialogs using the [Google Gemini API](https://ai.google.dev/).

---

## Quick Start

```bash
# 1. Clone / copy the project
# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=<your key>

# 4. Generate dialogs
python main.py generate --n 5 --seed 42 --out dataset.json

# 5. Analyze the dataset
python main.py analyze --input dataset.json --seed 42 --out results.json
```

---

## Commands

### `generate`

Generates N synthetic customer support dialogs and writes them to a JSON file.

```
python main.py generate [OPTIONS]

Options:
  --n       INT     Number of dialogs to generate  [default: 5]
  --seed    INT     Random seed for reproducibility [default: 42]
  --model   STR     Gemini model name               [default: gemini-2.0-flash]
  --out     PATH    Output file                     [default: dataset.json]
```

### `analyze`

Reads a dialog dataset and produces a structured analysis for each dialog.

```
python main.py analyze [OPTIONS]

Options:
  --input   PATH    Input dialog dataset            [default: dataset.json]
  --seed    INT     Seed used during generation (for traceability) [default: 42]
  --model   STR     Gemini model name               [default: gemini-2.0-flash]
  --out     PATH    Output file                     [default: results.json]
```

---

## Output Schemas

### `dataset.json` — list of `Dialog`

```json
{
  "id": "3f1b2c…",
  "scenario": "Customer cannot reset their password",
  "messages": [
    { "role": "customer", "content": "Hi, I can't reset my password." },
    { "role": "agent",    "content": "I'm sorry to hear that…" }
  ]
}
```

### `results.json` — list of `AnalysisResult`

```json
{
  "dialog_id": "3f1b2c…",
  "intent": "Reset account password",
  "satisfaction": "satisfied",
  "quality_score": 4,
  "mistake_codes": null,
  "raw_model_output": "…"
}
```

**`mistake_codes`** uses short identifiers:  
`WRONG_INFO` · `NO_EMPATHY` · `UNRESOLVED` · `POLICY_VIOLATION` · `SLOW_RESPONSE`

---

## Determinism

This tool is designed to be **as deterministic as possible**:

| Mechanism | Effect |
|---|---|
| `--seed` + `random.seed(seed)` | Scenario selection is reproducible |
| Per-dialog seed (`seed + i`) | Each dialog uses its own isolated `random.Random` |
| UUID5 with stable namespace | Dialog IDs are identical across runs for the same seed |
| `temperature=0` for analysis | Analysis output is near-deterministic |
| `temperature=0.7` for generation | Intentionally varied for realistic diversity |

> **Honest caveat:** Gemini (like all cloud LLMs) does not guarantee bit-identical outputs across API calls, even at `temperature=0`. Determinism is **best-effort**: the same seed will produce very similar results, but not necessarily byte-identical ones.

---

## Project Structure

```
ai_support_tool/
├── main.py           # CLI entry point (argparse)
├── requirements.txt
├── README.md
├── .env.example
└── src/
    ├── schema.py     # Pydantic v2 models
    ├── prompts.py    # Prompt templates + scenario pool
    ├── llm.py        # Gemini API calls + retry logic
    └── storage.py    # JSON read/write helpers
```

---

## Architecture Notes

The architecture is intentionally **flat and minimal**:

- **No abstract interfaces** — each module has a single, obvious responsibility.
- **No async** — synchronous code is easier to debug and reason about for a CLI tool.
- **No global state** — the API client is created per-command invocation.
- **Pydantic v2 `response_schema`** — lets Gemini return structured JSON directly, eliminating fragile regex parsing.
- **1 retry per call** — enough resilience for transient LLM failures without complexity.
- **`dialog_id` injected after parsing** — the LLM never needs to reproduce IDs; they are always deterministically derived from the seed.
