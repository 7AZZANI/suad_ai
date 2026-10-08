# Running a local LLM

The platform defaults to **Ollama** (OpenAI-compatible). Anything that speaks
the OpenAI `/v1/chat/completions` API works with the same adapter.

## Ollama (recommended default)

```bash
# Install: https://ollama.com
ollama serve                     # starts the API on :11434
ollama pull qwen3:4b             # small, fast, tool-capable
# optional, for RAG:
ollama pull nomic-embed-text
```

`.env` (already the default):

```ini
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=local
LLM_MODEL=qwen3:4b
```

Other good local models: `qwen3:8b`, `llama3.1:8b`, `mistral-nemo`. Set
`LLM_MODEL` to the pulled tag. Tool calling quality varies by model — Qwen3
and Llama 3.1 handle the tool loop well.

> If a small model struggles to emit valid tool calls, lower
> `LLM_TEMPERATURE` (e.g. `0.1`) or use a larger model.

## vLLM (high-throughput, GPU)

```bash
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-8B-Instruct --port 8001
```

```ini
LLM_PROVIDER=vllm
LLM_BASE_URL=http://localhost:8001/v1
LLM_API_KEY=local
LLM_MODEL=Qwen/Qwen3-8B-Instruct
```

## LM Studio (desktop GUI)

Enable the local server in LM Studio (OpenAI-compatible, default
`http://localhost:1234/v1`).

```ini
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=local
LLM_MODEL=<model shown in LM Studio>
```

## Verifying

```bash
curl -X POST http://localhost:8000/api/setup/test-llm
# {"ok": true, "provider": "ollama", "detail": "model=qwen3:4b"}
```

or **Setup Wizard → LLM** in the admin UI. A failing check returns a clear
message (base URL, model, cause) instead of a stack trace.

## Fully offline checklist

| Capability | Local option | Cloud-free? |
|---|---|---|
| LLM | Ollama / vLLM / LM Studio | ✅ |
| STT | faster-whisper | ✅ |
| TTS | Piper (or built-in tone fallback) | ✅ |
| RAG | Qdrant + Ollama embeddings | ✅ |
| Telephony | LiveKit + self-hosted SIP | ✅ |
| Database | SQLite or local Postgres | ✅ |

You can run the entire platform with no internet access.
