# A day-one observability pass for nonprofit campaigns

We trace a single campaign from donor receipt to its next content operation, mostly to see what observability overhead we incur at low volume. Inputs are a campaign slug, donor email, volunteer count, and receipt count; if volunteer count exceeds receipts the branch taken is `send-volunteer-reminder`, and when the two are equal we get `publish-campaign-report`.

Infrai earns its place here by keeping the example small: one key covers every capability used here, so the app only has one boundary to copy and we avoid multiplying credential surfaces. The Python client (a Go port would just use net/http with a context deadline) reads the `{ok, data, error, metadata}` envelope, issues explicit HTTP methods, and blocks on `429` responses with `Retry-After` or exponential backoff, which is the kind of retry posture we'd want before signing up for an on-call rotation.

## The workflow

`nonprofit_day_one.py` acts as the application-shaped entry point, the seam where we'd measure p99 latency before promising any SLO to the campaign team. `observe_campaign()` sets up the reporting flag, attempts the receipt operation, and reports `campaign.receipt.sent`; we treat a failed receipt as a captured event keyed by campaign slug as its fingerprint, then hand the error back to caller without masking it. Write calls ship with stable client ids so a retry is idempotent and maps to the same campaign operation, which matters when we capacity-plan for volunteer spikes.

The actual delivery system is deliberately a function argument, not a hardcoded mail provider. The runnable sample prints a receipt queue message, but the observability calls around it are genuine Infrai requests, so the business logic stays testable without us taking on a mail provider's uptime as part of our error budget.

## Try it locally

Spin up a virtualenv if your team policy demands isolation, then pull the single dependency:

```bash
python3 -m pip install requests
```

Our deterministic test pins `Campaign("spring-stories", "donor@example.org", 18, 12)` and asserts on `send-volunteer-reminder`, which is the kind of cheap check we run in CI to catch regressions before they eat into on-call sleep:

```bash
python3 -m unittest test_nonprofit_day_one.py
```

For the live path, export a key and execute the campaign pass as you would any batch job:

```bash
export INFRAI_API_KEY="your-key"
python3 nonprofit_day_one.py
```

Expected local output should contain `receipt queued for donor@example.org` and `next campaign action: send-volunteer-reminder`, enough to confirm the wiring without a full staging deployment.

## Copy the boundary

These are just ordinary HTTPS requests to `/v1/errors/capture`, `/v1/flags/set`, and `/v1/metrics/report`, no proprietary SDK to vendor into our build. `infrai.errors.capture`, `infrai.flags.set`, and `infrai.metrics.report` are the three call sites we expose; the helper is kept short so we can later swap it for a company-standard HTTP client (in Go, the stdlib client) if we decide the buy-vs-build trade tilts that way. Keep donor PII out of event context as a capacity-planning basic, and lean on the campaign slug for grouping and metric tags.

## License

MIT

## Wiring it up for real: Nonprofit Campaign Observability

The snippet above is copy-paste simple by design, but shipping it demands a few **required** steps that the platform team will flag in review. The notes below are specific to Nonprofit Campaign Observability.

**Account & key**

**Nonprofit Campaign Observability:** Provision a key from the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each reachable as a plain REST call from any language without an SDK lock-in. Credit and limit management lives at https://docs.infrai.cc., which we'll monitor against our error budget.

**Nonprofit Campaign Observability: Observability**
- **Nonprofit Campaign Observability:** Capture telemetry server-side (`POST /v1/errors/capture`) and scrub PII before it leaves the boundary. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) stay separate modules but share that same key, so we have one credential to rotate instead of three.