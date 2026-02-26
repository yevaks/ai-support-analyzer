"""Gemini API interactions for dialog generation and analysis."""

from __future__ import annotations

import json
import random
import re
import time
import uuid

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from src.prompts import (
    analyze_dialog_prompt,
    format_dialog_for_analysis,
    generate_dialog_prompt,
    pick_scenario,
)
from src.schema import AnalysisResult, Dialog

# Stable UUID namespace derived from a fixed DNS-style name.
_BASE_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "ai-support-tool")


def _dialog_id(seed: int, index: int) -> str:
    """Generate a deterministic UUID5 for dialog index i under a given seed."""
    ns = uuid.uuid5(_BASE_NAMESPACE, str(seed))
    return str(uuid.uuid5(ns, str(index)))


def _make_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def _call_with_rate_limit_retry(
    client: genai.Client,
    model: str,
    contents: str,
    config: types.GenerateContentConfig,
):
    """Call generate_content and retry once on 429, honouring retryDelay."""
    for attempt in range(2):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except genai_errors.ClientError as exc:
            exc_str = str(exc)
            is_rate_limit = "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str
            if not is_rate_limit or attempt == 1:
                raise
            # Try to extract retryDelay from the error message (e.g. "29s" or "29.216s").
            delay = 35.0  # safe default
            match = re.search(r'retryDelay.*?(\d+\.?\d*)', str(exc))
            if match:
                delay = float(match.group(1)) + 5  # +5s buffer
            print(f"  [rate-limit] 429 received, waiting {delay:.0f}s before retry…")
            time.sleep(delay)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate_dialogs(
    *,
    api_key: str,
    model: str,
    n: int,
    seed: int,
) -> list[Dialog]:
    """Generate N customer support dialogs using the Gemini API."""
    client = _make_client(api_key)
    random.seed(seed)

    dialogs: list[Dialog] = []

    for i in range(n):
        dialog_seed = seed + i
        rng = random.Random(dialog_seed)
        scenario = pick_scenario(rng)
        dialog_id = _dialog_id(seed, i)
        prompt = generate_dialog_prompt(scenario)

        print(f"[generate] dialog {i + 1}/{n}  id={dialog_id}  scenario='{scenario[:50]}'")

        dialog = _generate_one(
            client=client,
            model=model,
            prompt=prompt,
            dialog_id=dialog_id,
            scenario=scenario,
        )
        dialogs.append(dialog)

    return dialogs


def _generate_one(
    *,
    client: genai.Client,
    model: str,
    prompt: str,
    dialog_id: str,
    scenario: str,
) -> Dialog:
    """Call the API once (with one retry on validation failure)."""
    config = types.GenerateContentConfig(
        temperature=0.7,
        response_mime_type="application/json",
        response_schema=Dialog,
    )

    for attempt in range(2):
        response = _call_with_rate_limit_retry(
            client=client,
            model=model,
            contents=prompt,
            config=config,
        )
        raw = response.text or ""
        try:
            data = json.loads(raw)
            # Overwrite id and scenario to guarantee correctness.
            data["id"] = dialog_id
            data["scenario"] = scenario
            return Dialog.model_validate(data)
        except Exception as exc:
            if attempt == 0:
                print(f"  [warn] attempt 1 failed ({exc}), retrying…")
                continue
            raise RuntimeError(
                f"Dialog generation failed after 2 attempts.\n"
                f"Last error: {exc}\n"
                f"Raw output: {raw!r}"
            ) from exc

    # Unreachable, but satisfies type checkers.
    raise RuntimeError("Unexpected code path in _generate_one")


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def analyze_dialogs(
    *,
    api_key: str,
    model: str,
    dialogs: list[dict],
    seed: int,
) -> list[AnalysisResult]:
    """Analyse a list of dialog dicts and return AnalysisResult objects."""
    client = _make_client(api_key)
    results: list[AnalysisResult] = []

    for i, dialog in enumerate(dialogs):
        dialog_id = dialog.get("id", f"unknown-{i}")
        print(f"[analyze] dialog {i + 1}/{len(dialogs)}  id={dialog_id}")
        result = _analyze_one(
            client=client,
            model=model,
            dialog=dialog,
            dialog_id=dialog_id,
        )
        results.append(result)

    return results


def _analyze_one(
    *,
    client: genai.Client,
    model: str,
    dialog: dict,
    dialog_id: str,
) -> AnalysisResult:
    """Call the API for a single dialog (with one correction retry)."""
    dialog_text = format_dialog_for_analysis(dialog)
    prompt = analyze_dialog_prompt(dialog_text)

    # AnalysisResult without dialog_id so the LLM does not need to produce it.
    class _AnalysisPayload(AnalysisResult):
        dialog_id: None = None  # type: ignore[assignment]

    config = types.GenerateContentConfig(
        temperature=0,
        response_mime_type="application/json",
        response_schema=_AnalysisPayload,
    )

    last_error: Exception | None = None
    last_raw: str = ""

    for attempt in range(2):
        response = _call_with_rate_limit_retry(
            client=client,
            model=model,
            contents=prompt,
            config=config,
        )
        raw = response.text or ""
        last_raw = raw
        try:
            data = json.loads(raw)
            data["dialog_id"] = dialog_id
            data["raw_model_output"] = raw
            return AnalysisResult.model_validate(data)
        except Exception as exc:
            last_error = exc
            if attempt == 0:
                print(f"  [warn] attempt 1 failed ({exc}), retrying…")
                continue

    raise RuntimeError(
        f"Analysis failed for dialog {dialog_id!r} after 2 attempts.\n"
        f"Last error: {last_error}\n"
        f"Raw output: {last_raw!r}"
    )
