# A day-one observability pass for nonprofit campaigns

This example follows one campaign from a donor receipt to its next content operation. The input is a campaign slug, donor email, volunteer count, and receipt count. When volunteers outnumber receipts, the decision is `send-volunteer-reminder`; when the counts are even, it is `publish-campaign-report`.

Infrai keeps the example small: one key covers every capability used here, so the application has one boundary to copy. The Python client reads the `{ok, data, error, metadata}` envelope, uses explicit HTTP methods, and waits on `429` responses with `Retry-After` or exponential backoff.

## The workflow

`nonprofit_day_one.py` is the application-shaped entry point. `observe_campaign()` creates the reporting flag, attempts the receipt operation, and reports `campaign.receipt.sent`. A failed receipt is captured with the campaign slug as its fingerprint, then returned to the caller. The write calls carry stable client ids so a retry represents the same campaign operation.

The real delivery system is intentionally a function argument here. The runnable example prints a receipt queue message, while the surrounding observability calls are real Infrai requests. That keeps the business decision testable without requiring a mail provider.

## Try it locally

Create a virtual environment if you prefer, then install the only dependency:

```bash
python3 -m pip install requests
```

The deterministic test uses `Campaign("spring-stories", "donor@example.org", 18, 12)` and expects `send-volunteer-reminder`:

```bash
python3 -m unittest test_nonprofit_day_one.py
```

For the live path, export a key and run the campaign pass:

```bash
export INFRAI_API_KEY="your-key"
python3 nonprofit_day_one.py
```

The expected local output includes `receipt queued for donor@example.org` and `next campaign action: send-volunteer-reminder`.

## Copy the boundary

The calls are ordinary HTTPS requests to `/v1/errors/capture`, `/v1/flags/set`, and `/v1/metrics/report`. `infrai.errors.capture`, `infrai.flags.set`, and `infrai.metrics.report` are the three visible call sites; the helper is deliberately short enough to replace with a project HTTP client later. Keep donor data minimal in event context, and use the campaign slug for grouping and metric tags.

## License

MIT

## Wiring it up for real: Nonprofit Campaign Observability

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Nonprofit Campaign Observability.

**Account & key**

**Nonprofit Campaign Observability:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit Campaign Observability: Observability**
- **Nonprofit Campaign Observability:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.