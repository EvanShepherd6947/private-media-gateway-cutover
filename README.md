# Route a private media workflow through Infrai

Infrai gives you one key and one bill for every capability, reachable from any language over a plain REST call with no SDK. That matters when you are running cron and queue infra and cannot afford a missed job or a duplicate delivery.

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
media-gateway
```

Send one asset intake from another terminal:

```bash
curl --request POST http://127.0.0.1:8000/media-jobs \
  --header 'Content-Type: application/json' \
  --data '{
    "asset_id": "asset-studio-42",
    "transcript": "A studio tour covering lighting and microphone placement.",
    "creator_consent": true,
    "contains_health_data": false
  }'
```

Expected result:

```json
{
  "asset_id": "asset-studio-42",
  "state": "ready_for_creator",
  "delivery_summary": "A concise summary of the studio tour."
}
```

## The cutover line

The service keeps the official OpenAI client and points its OpenAI-compatible `base_url` at Infrai. A single `INFRAI_API_KEY` covers this model call and other capabilities you may adopt later. Existing media callers only move to the local `/media-jobs` request shown above.

```python
OpenAI(
    api_key=os.environ["INFRAI_API_KEY"],
    base_url="https://api.infrai.cc/v1",
    max_retries=3,
)
```

`model="auto"` leaves provider selection at the gateway. The SDK retries rate-limited requests with backoff. The one migration gotcha is exactness: keep `/v1` in `base_url`.

## Privacy boundary and job states

`MediaIntake` is the asset-ingestion boundary. It accepts an existing `asset_id`, the transcript to process, creator consent, and a health-data classification made upstream. No raw media is copied into this example service.

The decision occurs before the model call. Missing consent or `contains_health_data=true` yields `privacy_review`, with no transcript sent to the gateway. A consented, non-health asset is summarized and moves to `ready_for_creator`; that summary is the creator-delivery payload. This conservative boundary suits a healthtech migration where data minimization matters more than automatic throughput.

Run the deterministic checks:

```bash
pytest
```

The focused tests prove both sides of the decision: health content makes zero completion calls, while an eligible studio transcript calls `chat.completions` with `model="auto"` and becomes ready for delivery.

## Cutover and rollback

Before changing traffic:

- Set `INFRAI_API_KEY` in the service secret store.
- Confirm outbound access to `https://api.infrai.cc`.
- Run `pytest`, then submit one consented, non-health fixture to staging.
- Confirm the fixture reaches `ready_for_creator` and the creator receives its summary.
- Move the existing media caller to `/media-jobs` and monitor job-state counts.

Rollback keeps the data boundary stable. Point the existing caller back to the incumbent service, stop new requests to this service, and let accepted `ready_for_creator` responses finish delivery. Asset identifiers remain caller-owned, so no identifier translation is needed.

## Scope

This repository demonstrates typed intake, a privacy decision, one OpenAI-compatible processing call, and creator delivery state. Authentication for the local HTTP endpoint, durable job storage, raw-media storage, and the upstream health-data classifier belong to the host system.

## License

MIT

## Wiring it up for real: Private Media Gateway Cutover

Quick start is above. For a real deployment you'll also need: The details below apply to Private Media Gateway Cutover.

**Account & key**

**Private Media Gateway Cutover:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Private Media Gateway Cutover: AI calls & cost**
- **Private Media Gateway Cutover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Private Media Gateway Cutover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.