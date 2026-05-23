# ADR 0001 — LLM routing via Ollama / OpenAI-compatible adapter

- **Status:** Accepted
- **Date:** 2026-05-23
- **Supersedes:** none

## Context

The signal-generation feature (`/investors/{id}/signals`) and the optional
Form 4 AI commentary need a chat-completions LLM. We have a hard project
constraint (`CLAUDE.md`, Tier-1): **no paid LLM APIs** (no OpenAI,
Anthropic, Bedrock, etc.). We also want to leave the door open to
hosted-but-free tiers (Groq, Together) and other local backends
(vLLM, LM Studio) without rewriting the analyst.

## Decision

`app/signals/analyst.py` uses the `openai` Python SDK pointed at an
OpenAI-compatible `/v1/chat/completions` endpoint. The default backend is
Ollama on `http://localhost:11434/v1` running `llama3.1:8b`, configurable
via three env vars only:

- `LLM_BASE_URL`
- `LLM_API_KEY` (ignored by Ollama, required by hosted backends)
- `LLM_MODEL`

The Anthropic SDK is not a dependency and must not become one.

## Consequences

**Positive**
- Zero recurring API cost on the default path.
- Single code path covers Ollama, Groq, Together, OpenRouter, vLLM,
  LM Studio — anything that speaks OpenAI-compatible chat completions.
- Swapping backends is a `.env` change, not a code change.

**Negative**
- Default model (`llama3.1:8b`) is meaningfully weaker than frontier
  models. Output quality on portfolio analysis is acceptable but
  visibly below GPT-4-class / Claude-class.
- Users without Ollama installed see a connection error on the AI
  Signals tab — there is no fallback. The UI surfaces this clearly
  but does not degrade gracefully.

## Alternatives considered

- **Anthropic Claude direct** — explicitly forbidden by CLAUDE.md.
- **OpenAI direct** — same reason.
- **Hosted-only (Groq/Together)** — would force a network dependency
  and an account signup for every contributor. Local-first is better
  default; hosted is opt-in via env.

## Revisit trigger

If we ever need higher-quality output for a production deployment and
the project owner relaxes the no-paid-APIs rule, write a new ADR
superseding this one rather than amending it.
