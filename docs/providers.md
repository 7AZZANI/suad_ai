# Providers — swap vendors & add adapters

Every external capability is behind an **interface + adapter + factory**. The
rest of the app depends only on the interface. There are no hardcoded vendors.

```
app/providers/<kind>/
  base.py        # the interface (abstract) + data types
  *_adapter.py   # one concrete adapter per vendor
  factory.py     # get_<kind>() — picks an adapter from settings (lru_cache)
```

| Kind | Interface | Adapters shipped |
|---|---|---|
| LLM | `LLMProvider` | `OpenAICompatibleLLM` (Ollama/vLLM/LM Studio/OpenRouter/OpenAI/DashScope), `AnthropicLLM` |
| STT | `STTProvider` | `FasterWhisperSTT`, `NullSTT` |
| TTS | `TTSProvider` | `PiperTTS`, `XTTS`, `NullTTS` (offline tone) |
| Telephony | `TelephonyProvider` | `LiveKitSIPTelephony`, `TwilioTelephony` |
| Memory | `MemoryProvider` | `QdrantMemory`, `NullMemory` |

Heavy SDKs (`openai`, `anthropic`, `faster-whisper`, `qdrant-client`,
`livekit`) are **imported lazily inside adapters**, so the platform boots with
only `requirements-core.txt` and you only pay for what you use.

## Switching LLM provider (just `.env`)

```ini
# Local Ollama (default)
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=local
LLM_MODEL=qwen3:4b

# OpenRouter
LLM_PROVIDER=openrouter
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-...
LLM_MODEL=qwen/qwen3-32b

# OpenAI
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4.1-mini

# Anthropic Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4
```

Restart the backend. Verify on **Setup Wizard → LLM** or
`POST /api/setup/test-llm`.

## Add a new LLM adapter

If the vendor is OpenAI-compatible you need **zero code** — just set
`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL` and add its name to
`_OPENAI_COMPATIBLE` in `app/providers/llm/factory.py`.

For a genuinely different protocol:

1. Create `app/providers/llm/myvendor_adapter.py`:

   ```python
   from app.providers.llm.base import LLMProvider, LLMResponse
   from app.providers.base import ProviderStatus

   class MyVendorLLM(LLMProvider):
       name = "myvendor"
       async def chat(self, messages, tools=None, *, temperature=None, max_tokens=None):
           ...  # call your API, map tool calls to LLMResponse(tool_calls=[...])
       async def health(self) -> ProviderStatus:
           ...
   ```

2. Wire it in `app/providers/llm/factory.py`:

   ```python
   if provider == "myvendor":
       return MyVendorLLM(...)
   ```

3. Done — the agent runtime, tools, and UI need no changes.

The same three-step pattern applies to STT/TTS/telephony/memory: implement the
`base.py` interface, register in that kind's `factory.py`.

## Embeddings

RAG embeddings use any OpenAI-compatible `/embeddings` endpoint over plain
`httpx` (`app/providers/memory/embeddings.py`) — Ollama's `nomic-embed-text`
by default, or OpenAI's `text-embedding-3-*`. Set `EMBEDDING_*` in `.env`.
