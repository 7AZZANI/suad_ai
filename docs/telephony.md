# Telephony

The telephony layer normalizes any vendor's inbound events into a single
`CallEvent` and renders replies through the vendor's `TelephonyResponse`. Call
handling logic is therefore **provider-independent**.

```
inbound webhook ──> provider.parse_webhook() ──> CallEvent
                                                    │
                          agent_service.chat()  <───┘
                                                    │
TelephonyResponse <── provider.render_response() <──┘  (TwiML / JSON)
```

Endpoints (see `app/api/routes/telephony.py`):

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/telephony/status` | Active provider + configured flag |
| `GET` | `/api/telephony/calls` | Call log history |
| `POST` | `/api/telephony/livekit/webhook` | LiveKit/SIP inbound events |
| `POST` | `/api/telephony/twilio/webhook` | Twilio voice webhook |

## Local-first: LiveKit + SIP (default)

```ini
TELEPHONY_PROVIDER=livekit_sip
LIVEKIT_URL=wss://your-livekit-host
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

The adapter parses LiveKit SIP JSON events and returns a JSON action
(`say` / `gather` / `hangup`) for a `livekit-agents` worker to execute. Until
credentials are set it is a **functional placeholder**: webhook parsing and
the agent loop work offline, only live media bridging needs the worker +
a SIP trunk. Run a worker with `pip install -r requirements.txt` then your
`livekit-agents` entrypoint pointed at this backend.

## Cloud option: Twilio

```ini
TELEPHONY_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
```

Point your Twilio number's Voice webhook at
`https://<your-host>/api/telephony/twilio/webhook`. The adapter parses the
form-encoded request and renders **TwiML** (`<Gather input="speech dtmf">`),
looping speech back into the agent until hangup.

## Simulate a call without any provider

```bash
curl -X POST http://localhost:8000/api/telephony/twilio/webhook \
  -d 'CallSid=CA123&From=%2B15550001111&To=%2B15550002222&SpeechResult=what is the status of order 1001'
```

You get TwiML back and a row appears under **Call Logs**.

## Adding a new phone vendor

Implement `TelephonyProvider` (`parse_webhook`, `render_response`, `status`)
in `app/providers/telephony/<vendor>_adapter.py`, register it in
`factory.py` and the `_ADAPTERS` map in the telephony route. No changes to the
agent or call-handling code.
