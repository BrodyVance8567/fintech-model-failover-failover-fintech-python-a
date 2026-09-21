"""Domain models and the payment action policy."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Callable

from pydantic import BaseModel, Field


class PaymentEvent(BaseModel):
    event_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    amount_minor: int = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    merchant: str = Field(min_length=1)
    risk_signals: list[str] = Field(default_factory=list)


class RiskAction(StrEnum):
    APPROVE = "approve"
    MANUAL_REVIEW = "manual_review"


class Assessment(BaseModel):
    recommendation: str
    notification: str
    rationale: str


class AuditNotification(BaseModel):
    event_id: str
    account_id: str
    message: str
    action: RiskAction
    reason: str
    model_vendor: str
    model_request_id: str


class RiskDecision(BaseModel):
    action: RiskAction
    notification: AuditNotification


class PaymentRiskService:
    """Keep the irreversible decision in code; use the model as an analyst."""

    def __init__(
        self,
        analyst: Callable[[PaymentEvent], Any],
        manual_review_threshold_minor: int = 100_000,
    ) -> None:
        self._analyst = analyst
        self._threshold = manual_review_threshold_minor

    def decide(self, event: PaymentEvent) -> RiskDecision:
        routed = self._analyst(event)
        policy_requires_review = bool(event.risk_signals) or event.amount_minor >= self._threshold
        model_requests_review = routed.assessment.recommendation == "review"
        action = (
            RiskAction.MANUAL_REVIEW
            if policy_requires_review or model_requests_review
            else RiskAction.APPROVE
        )
        reason = (
            "payment policy requires review"
            if policy_requires_review
            else routed.assessment.rationale
        )
        notification = AuditNotification(
            event_id=event.event_id,
            account_id=event.account_id,
            message=routed.assessment.notification,
            action=action,
            reason=reason,
            model_vendor=routed.vendor,
            model_request_id=routed.request_id,
        )
        return RiskDecision(action=action, notification=notification)
