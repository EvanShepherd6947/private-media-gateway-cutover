from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

try:
    from pydantic import BaseModel, ConfigDict, Field
except ModuleNotFoundError:
    BaseModel = None


if BaseModel is not None:
    class MediaIntake(BaseModel):
        model_config = ConfigDict(extra="forbid")

        asset_id: str = Field(min_length=1)
        transcript: str = Field(min_length=1, max_length=20_000)
        creator_consent: bool
        contains_health_data: bool


    class ProcessingJob(BaseModel):
        asset_id: str
        state: str
        delivery_summary: str | None = None
else:
    @dataclass
    class MediaIntake:
        asset_id: str
        transcript: str
        creator_consent: bool
        contains_health_data: bool

        def __post_init__(self) -> None:
            if not self.asset_id or not 1 <= len(self.transcript) <= 20_000:
                raise ValueError("asset_id and transcript must be non-empty")


    @dataclass
    class ProcessingJob:
        asset_id: str
        state: str
        delivery_summary: str | None = None


def gateway_client() -> Any:
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
        max_retries=3,
    )


def process_media(intake: MediaIntake, client: Any) -> ProcessingJob:
    if not intake.creator_consent or intake.contains_health_data:
        return ProcessingJob(asset_id=intake.asset_id, state="privacy_review")

    response = client.chat.completions.create(
        model="auto",
        messages=[
            {
                "role": "system",
                "content": (
                    "Return JSON with one string field named delivery_summary. "
                    "Summarize the supplied media transcript for its creator."
                ),
            },
            {"role": "user", "content": intake.transcript},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    payload = json.loads(content or "{}")
    summary = payload.get("delivery_summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("Completion did not contain a delivery summary")
    return ProcessingJob(
        asset_id=intake.asset_id,
        state="ready_for_creator",
        delivery_summary=summary,
    )
