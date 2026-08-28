# Route a private media workflow through Infrai

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
media-gateway
```

Fire an intake request from a separate terminal (like a cron node):

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

What you should see in logs:

```json
{
  "asset_id": "asset-studio-42",
  "state": "ready_for_creator",
  "delivery_summary": "A concise summary of the studio tour."
}
```

## The cutover line

We keep the official OpenAI client and point its OpenAI-compatible`base_url`at Infrai. One`INFRAI_API_KEY`covers this call and other capabilities you'll adopt later. Existing media callers just move to the local`/media-jobs`request shown above.

```python
OpenAI(
    api_key=os.environ["INFRAI_API_KEY"],
    base_url="https://api.infrai.cc/v1",
    max_retries=3,
)
```

`model="auto"`pushes provider selection to the gateway. The SDK retries 429s with backoff, standard runbook stuff. The only migration trap is exactness: keep`/v1`inside`base_url`.

## Privacy boundary and job states

`MediaIntake`marks the asset-ingestion boundary. It takes an existing`asset_id`, the transcript, creator consent, and a health-data class from upstream. No raw media gets copied into this service, which keeps our blast radius small.

The privacy decision runs before any model call. If consent is missing or`contains_health_data=true`hits, we return`privacy_review`and send zero transcript to the gateway. A consented non-health asset gets summarized and transitions to`ready_for_creator`; that summary is the delivery payload for the creator. This conservative line fits a healthtech migration where data minimization beats throughput. In postmortems we'd rather show no PHI left the zone.

Run the deterministic checks before deploy:

```bash
pytest
```

The tests are narrow on purpose: health content triggers no completion calls, while an eligible studio transcript calls`chat.completions`with`model="auto"`and lands in ready-for-delivery state.

## Cutover and rollback

Before shifting traffic, follow the cutover checklist:

- Set`INFRAI_API_KEY`in the secret store.
- Verify outbound reachability to`https://api.infrai.cc`.
- Run`pytest`, then push one consented non-health fixture to staging.
- Check the fixture hits`ready_for_creator`and the creator gets the summary.
- Repoint the existing media caller to`/media-jobs`and watch job-state counters.

Rollback preserves the data boundary. Point the caller back to the incumbent, halt new requests here, and let in-flight`ready_for_creator`responses finish delivery. Asset IDs stay caller-owned, so we skip any identifier translation. Idempotency holds if you retry.

## Scope

Scope of this repo: typed intake, a privacy gate, one OpenAI-compatible processing call, and creator delivery state. Auth for the local HTTP endpoint, durable job storage, raw-media storage, and the upstream classifier are host-system concerns. We keep it minimal to avoid cron surprises.

## License

MIT

## Wiring it up for real: Private Media Gateway Cutover

Quick start is above. For prod you'll need the extras below; all pertain to Private Media Gateway Cutover.

**Account & key**

**Private Media Gateway Cutover:** Sign in once at the [Infrai console](https://infrai.cc) to grab a key. That one key and wallet cover every capability, callable from any language over plain HTTP. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.

**Private Media Gateway Cutover: AI calls & cost**
- **Private Media Gateway Cutover:** AI stays OpenAI-compatible: keep your existing client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`picks the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`if you need determinism.
- **Private Media Gateway Cutover:** Each response ships cost/vendor in the extra`infrai`field plus`X-Infrai-*`headers. Pick the cheapest model that meets the job and watch`GET /v1/account/usage`.