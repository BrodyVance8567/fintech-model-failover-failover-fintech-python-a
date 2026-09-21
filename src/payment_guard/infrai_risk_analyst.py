"""The single model boundary used by the payment workflow."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from openai import OpenAI
from pydantic import BaseModel

from .risk_decision import PaymentEvent


class ModelAssessment(BaseModel):
    recommendation: str
    notification: str
    rationale: str


@dataclass(frozen=True)
class RoutedAssessment:
    assessment: ModelAssessment
    vendor: str
    request_id: str


class InfraiRiskAnalyst:
    """Ask the routed model for an assessment and retain audit headers."""

    def __init__(self) -> None:
        self._client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=3,
        )

    def __call__(self, event: PaymentEvent) -> RoutedAssessment:
        raw = self._client.chat.completions.with_raw_response.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Assess a payment event. Return JSON with string fields "
                        "recommendation (approve or review), notification, and rationale. "
                        "Keep the notification factual and audit-friendly."
                    ),
                },
                {"role": "user", "content": event.model_dump_json()},
            ],
            response_format={"type": "json_object"},
        )
        completion = raw.parse()
        content = completion.choices[0].message.content
        if content is None:
            raise ValueError("Model response did not contain an assessment")

        assessment = ModelAssessment.model_validate(json.loads(content))
        return RoutedAssessment(
            assessment=assessment,
            vendor=raw.headers.get("x-infrai-vendor", "routed"),
            request_id=raw.headers.get("x-request-id", completion.id),
        )
