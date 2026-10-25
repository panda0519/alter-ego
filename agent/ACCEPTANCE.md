# Agent37 connector acceptance

Live Agent37 acceptance for instance `gr7nnwqxgf` was verified on 2026-10-25.
A POST to `http://127.0.0.1:8787/api/assistant` returned HTTP 200 with `{ source: "agent37", text }`.
The local preview then showed "Powered by Agent37" after that reply. The connector code remains fail-closed. Port 9119 was not used. No API key and no `a37_token` value are stored in this repository.

## Path

1. `frontend/src/AquaChat.tsx` sends the question to `askAssistant`.
2. `frontend/src/data/assistant.ts` always prepares a deterministic answer from the loaded `agent_context.json`.
3. If `VITE_AGENT_PROXY_URL` is a safe `/api/...` path, a localhost `/api/...` URL, or a public HTTPS URL with no credentials, query, or hash, the browser POSTs only the question, station id, and chart method to that proxy. It does not send a bearer token.
4. `agent/proxy/server.mjs` listens on `127.0.0.1:8787` by default and accepts only `POST /api/assistant`.
5. `agent/proxy/assistant-core.mjs` reads `AGENT37_API_URL`, `AGENT37_API_KEY`, and `AGENT_CONTEXT_URL` from the server environment. It forwards a bounded context to the operator-supplied OpenAI-style endpoint. A browser-supplied upstream URL is rejected.

A reply is labelled Agent37 only when the proxy returns `{ source: "agent37", text }`. If the proxy is unset, sleeping, unauthorized, or returns anything else, Aqua keeps the export briefing. "Powered by Agent37" is shown only after such a reply. Instance `gr7nnwqxgf` may be named. That name is not proof of a live answer.

## Local activation

Set `AGENT37_API_URL`, `AGENT37_API_KEY`, and `AGENT_CONTEXT_URL` only in the server environment. Do not put them in `VITE_` variables, frontend source, or Git.

From the repository root:

```
node agent/proxy/server.mjs
```

The proxy listens at `http://127.0.0.1:8787/api/assistant`. Then set `VITE_AGENT_PROXY_URL=http://127.0.0.1:8787/api/assistant` and rebuild the frontend.

The completion that satisfied this check came from the redacted endpoint pattern `https://gr7nnwqxgf-8000.agent37.app/v1/chat/completions`. The server sends the workspace key only from its own environment. Port 8000 was not listening at the start of the check, so an OpenAI-compatible adapter was started inside the instance. It forwards to that instance's Hermes gateway and is not part of this repository. A sleep or rebuild of the instance stops that process until it is started again. The published Render build does not set `VITE_AGENT_PROXY_URL`.

## Hosting

The Render site remains one static site. This connector does not create a second hosted service. Live local acceptance against instance `gr7nnwqxgf` was verified on 2026-10-25 with a real `{ source: "agent37", text }` reply. The public Render deployment remains fail-closed on the deterministic export briefing unless a proxy is configured. The static build answers from the published export when the proxy is absent.
