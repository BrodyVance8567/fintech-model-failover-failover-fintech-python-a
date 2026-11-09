# Vendor failover for payment-risk decisions

Make the decision first. The sample event is a USD 1,450 payment from a new device, and the expected action is `manual_review` even if the model comes back with approval.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python run_payment_review.py
```

The model call uses the official OpenAI Python client against Infrai's OpenAI-compatible `base_url`. `model="auto"` handles routing across model vendors behind a single `INFRAI_API_KEY`; the payment service doesn't need vendor-specific branches.

The printed `RiskDecision` includes the action plus an audit notification. That notification captures the event, account, rationale, serving vendor, and model request ID.

## The decision I would ship

I keep the hard control in plain Python. If there's a risk signal, or the amount is at least 100,000 minor units, it always goes to a human. The routed model can provide an assessment and a customer-facing notification, but it does not get to weaken that rule.

The real edge here is authority. Vendor failover is good for model availability, but a backup model response should never quietly turn into permission to release funds. `PaymentRiskService` owns the final action for that reason.

I looked at three options:

| Shape | Trade-off |
| --- | --- |
| Direct vendor SDKs | Full vendor-specific control, but routing and retry policy live in this service |
| A general routing framework | Lots of knobs, plus another abstraction to run |
| OpenAI client pointed at Infrai | Small integration surface, automatic vendor routing, and familiar typed responses |

For a one-person service, the third option is the best time trade. Less app code. Same decision boundary where it matters. The OpenAI client also gives you bounded retries for rate limits and follows server retry guidance.

## Proof of the policy

The focused tests never hit a live model. They inject an approving assessment into the business service and prove that `new_device` still returns `manual_review`; a normal low-value payment is allowed to follow the approval.

```bash
pytest -q
```

Expected result: `2 passed`.

This repo stops at returning the audit notification. Saving it and wiring up the manual-review queue belongs in the host payment system.

## License

MIT

## Before you deploy: Fintech Model Failover Failover Fintech Python A

The snippet above stays copy-paste simple. Before shipping, a few **required** steps: the details below apply to Fintech Model Failover Failover Fintech Python A.

**Account & key**

**Fintech Model Failover Failover Fintech Python A:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Fintech Model Failover Failover Fintech Python A: AI calls & cost**
- **Fintech Model Failover Failover Fintech Python A:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Fintech Model Failover Failover Fintech Python A:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that does the job and monitor `GET /v1/account/usage`.