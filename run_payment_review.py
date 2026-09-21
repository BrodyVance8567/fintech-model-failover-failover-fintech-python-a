"""Run one observable payment decision against Infrai."""

from payment_guard.infrai_risk_analyst import InfraiRiskAnalyst
from payment_guard.risk_decision import PaymentEvent, PaymentRiskService


def main() -> None:
    event = PaymentEvent(
        event_id="evt_2026_09_04_001",
        account_id="acct_2048",
        amount_minor=145_000,
        currency="USD",
        merchant="Northwind Components",
        risk_signals=["new_device"],
    )
    decision = PaymentRiskService(InfraiRiskAnalyst()).decide(event)
    print(decision.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
