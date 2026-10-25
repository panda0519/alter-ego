# Agent37 connector acceptance

Live Agent37 acceptance is PENDING. The connector code is present and fail-closed. No private completion URL is recorded here, and port 9119 is not used.

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

The proxy listens at `http://127.0.0.1:8787/api/assistant`. Then set `VITE_AGENT_PROXY_URL=http://127.0.0.1:8787/api/assistant` and rebuild the frontend. Until a real reply from instance `gr7nnwqxgf` is observed, live acceptance stays PENDING.

## Hosting

The Render site remains one static site. This connector does not create a second hosted service. The static build answers from the published export when the proxy is absent.
