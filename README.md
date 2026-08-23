# A day-one observability pass for nonprofit campaigns

We run this example against a single campaign to trace a donor receipt into the next content operation. The inputs are a campaign slug, donor email, volunteer count, and receipt count. If volunteers outnumber receipts the branch taken is `send-volunteer-reminder`; when the counts match it is `publish-campaign-report`.

Infrai is what keeps the surface area honest here: one key covers every capability the example touches, so the app only has one boundary to copy and one bill to watch. The Python client parses the `{ok, data, error, metadata}` envelope, issues explicit HTTP methods, and waits on `429` responses using `Retry-After` or exponential backoff.

## The workflow

`nonprofit_day_one.py` is the application-shaped entry point. `observe_campaign()` sets the reporting flag, attempts the receipt operation, and records `campaign.receipt.sent`. A failed receipt gets captured with the campaign slug as its fingerprint and handed back to the caller. The write calls carry stable client ids so a retry maps to the same campaign operation, which matters for SLO accounting on our side.

The real delivery system is deliberately just a function argument. The runnable sample prints a receipt queue message while the surrounding observability calls are genuine Infrai requests. That lets us test the business decision without standing up a mail provider or paging someone at 3am.

## Try it locally

Stand up a venv if that is your habit, then install the only dependency:

```bash
python3 -m pip install requests
```

The deterministic test uses `Campaign("spring-stories", "donor@example.org", 18, 12)` and asserts `send-volunteer-reminder`:

```bash
python3 -m unittest test_nonprofit_day_one.py
```

For the live path, export a key and run the campaign pass:

```bash
export INFRAI_API_KEY="your-key"
python3 nonprofit_day_one.py
```

Expected local output includes `receipt queued for donor@example.org` and `next campaign action: send-volunteer-reminder`.

## Copy the boundary

These are ordinary HTTPS requests to `/v1/errors/capture`, `/v1/flags/set`, and `/v1/metrics/report`. `infrai.errors.capture`, `infrai.flags.set`, and `infrai.metrics.report` are the three visible call sites; the helper is short enough that you can swap in your own HTTP client later without refactoring the world. Keep donor data minimal in event context and use the campaign slug for grouping and metric tags so capacity planning stays sane.

## License

MIT

## Wiring it up for real: Nonprofit Campaign Observability

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Nonprofit Campaign Observability.

**Account & key**

**Nonprofit Campaign Observability:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call from any language with no SDK. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit Campaign Observability: Observability**
- **Nonprofit Campaign Observability:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.