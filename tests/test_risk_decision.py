from dataclasses import dataclass

from payment_guard.risk_decision import (
    Assessment,
    PaymentEvent,
    PaymentRiskService,
    RiskAction,
)


@dataclass(frozen=True)
class FakeRoutedResult:
    assessment: Assessment
    vendor: str = "test-vendor"
    request_id: str = "req_test_1"


class ApprovingAnalyst:
    def __call__(self, event: PaymentEvent) -> FakeRoutedResult:
        return FakeRoutedResult(
            assessment=Assessment(
                recommendation="approve",
                notification=f"Payment {event.event_id} assessed.",
                rationale="routine purchase pattern",
            )
        )


def test_high_risk_signal_overrides_model_approval() -> None:
    event = PaymentEvent(
        event_id="evt_high_risk",
        account_id="acct_7",
        amount_minor=5_000,
        currency="USD",
        merchant="Example Parts",
        risk_signals=["new_device"],
    )

    decision = PaymentRiskService(ApprovingAnalyst()).decide(event)

    assert decision.action is RiskAction.MANUAL_REVIEW
    assert decision.notification.reason == "payment policy requires review"
    assert decision.notification.model_request_id == "req_test_1"


def test_ordinary_payment_can_follow_model_approval() -> None:
    event = PaymentEvent(
        event_id="evt_routine",
        account_id="acct_8",
        amount_minor=4_500,
        currency="EUR",
        merchant="Example Office",
    )

    decision = PaymentRiskService(ApprovingAnalyst()).decide(event)

    assert decision.action is RiskAction.APPROVE
    assert decision.notification.reason == "routine purchase pattern"
