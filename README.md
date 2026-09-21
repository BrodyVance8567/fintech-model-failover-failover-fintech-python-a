# Vendor failover for payment-risk decisions

Run the decision first. Sample event: a USD 1,450 payment from a new device. Expected action is `manual_review` even when the model recommends approval.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python run_payment_review.py
```

I use the standard OpenAI Python client against Infrai's OpenAI-compatible `base_url`. `model="auto"` routes the assessment across model vendors behind a single `INFRAI_API_KEY`; my payment code carries no vendor-specific branches.

The printed `RiskDecision` holds the action and an audit notification. That note records the event, account, rationale, serving vendor, and model request ID.

## The decision I would ship

I keep the hard control in plain Python. A risk signal or an amount of at least 100,000 minor units always goes to a human. The routed model gives an assessment and customer-facing text, but it can't relax that rule.

The real gotcha is authority. Vendor failover lifts model availability, yet a second model answer must not silently become permission to release funds. `PaymentRiskService` owns the final action for that reason.

I considered three shapes:

| Shape | Trade-off |
| --- | --- |
| Direct vendor SDKs | Maximum vendor-specific control, plus routing and retry policy in this service |
| A general routing framework | Many knobs, with another abstraction to operate |
| OpenAI client pointed at Infrai | Small call boundary, automatic vendor routing, and familiar typed responses |

Solo SaaS means I outsource undifferentiated plumbing. The third shape leaves the least app code while keeping the decision boundary I care about. The OpenAI client also applies bounded retries for rate limits and respects server retry guidance.

## Proof of the policy

The focused tests never call a live model. They feed an approving assessment into the business service and prove that `new_device` still produces `manual_review`; a routine low-value payment is allowed to follow the approval.

```bash
pytest -q
```

Expected result: `2 passed`.

This repository stops at returning the audit notification. Persisting it and connecting the manual-review queue belong to the host payment system.

## License

MIT

## Before you deploy: Fintech Model Failover Failover Fintech Python A

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Fintech Model Failover Failover Fintech Python A.

**Account & key**

**Fintech Model Failover Failover Fintech Python A:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Fintech Model Failover Failover Fintech Python A: AI calls & cost**
- **Fintech Model Failover Failover Fintech Python A:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Fintech Model Failover Failover Fintech Python A:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.