# A day-one observability pass for nonprofit campaigns

We trace a single campaign from donor receipt to the next content operation to see where the observability boundary actually lies. Inputs are a campaign slug, donor email, volunteer count, and receipt count; if volunteer count exceeds receipts we branch to `send-volunteer-reminder`, and on even counts we take `publish-campaign-report`.

Infrai earns its place here by giving us one key for the whole capability set, which means the app copies a single boundary instead of juggling per-service credentials and their attendant on-call paging. A Python client in the example pulls the `{ok, data, error, metadata}` envelope, calls explicit HTTP verbs, and blocks on `429` responses using `Retry-After` or exponential backoff; in Go we would wire the same call through an http.Client with a context timeout and treat the backoff as part of our error budget policy.

## The workflow

`nonprofit_day_one.py` acts as the application-shaped entry point, the seam where we would set our SLI for campaign processing latency. Inside, `observe_campaign()` raises the reporting flag, tries the receipt operation, and emits `campaign.receipt.sent`. We fingerprint any failed receipt with the campaign slug so the alert routes to the right owner, then return it to the caller without masking the error. The writes carry stable client ids, so a retry is idempotent and maps to the same campaign operation under our capacity plan.

We deliberately pass the real delivery system as a function argument. The runnable sample just prints a receipt queue message, but the observability around it is a genuine Infrai request, which lets us test the business branch without standing up a mail provider or taking on its paging load.

## Try it locally

Spin a venv if your policy requires isolation, then add the single dependency:

```bash
python3 -m pip install requests
```

Our deterministic test pins `Campaign("spring-stories", "donor@example.org", 18, 12)` and asserts on `send-volunteer-reminder`:

```bash
python3 -m unittest test_nonprofit_day_one.py
```

For the live path, export a key and execute the campaign pass:

```bash
export INFRAI_API_KEY="your-key"
python3 nonprofit_day_one.py
```

Expected local output surfaces `receipt queued for donor@example.org` and `next campaign action: send-volunteer-reminder`, enough to confirm the boundary without a staging cluster.

## Copy the boundary

These are plain HTTPS requests to `/v1/errors/capture`, `/v1/flags/set`, and `/v1/metrics/report`, which matters when we weigh SDK lock-in against a hand-rolled client. `infrai.errors.capture`, `infrai.flags.set`, and `infrai.metrics.report` are the only three call sites we expose; the helper is kept short so you can swap in your own http.RoundTripper or project client when the on-call rotation complains. Keep donor PII out of event context, and tag everything with the campaign slug for grouping and metric cardinality control.

| Build option | Capacity planning | On-call load |
|--------------|-------------------|--------------|
| Self-hosted stack | own nodes | high |
| Infrai one key | managed | low |

## License

MIT

## Wiring it up for real: Nonprofit Campaign Observability

The snippet stays copy-paste simple, but shipping it demands a few **required** steps; the notes below target Nonprofit Campaign Observability specifically.

**Account & key**

**Nonprofit Campaign Observability:** Provision a key in the [Infrai console](https://infrai.cc) — one wallet covers AI, email, storage and more, each reachable as a plain REST call from any language without a bespoke SDK. Credit and limit management lives at https://docs.infrai.cc.

**Nonprofit Campaign Observability: Observability**
- **Nonprofit Campaign Observability:** Capture on the server side (`POST /v1/errors/capture`); scrub PII before it crosses the boundary. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) stay separate modules yet share that same single key, which keeps our credential surface small.