"""Pydantic v2 data models for dialogs and analysis results."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["customer", "agent"]
    content: str


class Dialog(BaseModel):
    id: str
    scenario: str
    messages: list[Message]


class AnalysisResult(BaseModel):
    dialog_id: Optional[str] = None
    intent: str
    satisfaction: Literal["satisfied", "neutral", "unsatisfied"]
    quality_score: int = Field(ge=1, le=5)
    mistake_codes: Optional[list[str]] = None
    raw_model_output: Optional[str] = None
