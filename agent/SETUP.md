# Agent37 preparation and verification

Agent37 account: VERIFIED by the user's explicit confirmation on 2026-10-24.
Live integration: PENDING / OPTIONAL. The user confirms there is no active
instance or public URL. Core application, ML export integration and deployment
are independent of Agent37. The backup integration is disabled by default.
A local fixture/context-file check is not an
Agent37 conversation or sponsor integration evidence.

The Render site remains one static dashboard. Aqua can also call the optional
local proxy in `agent/proxy/server.mjs`, which delegates to
`agent/proxy/assistant-core.mjs`. The browser uses `VITE_AGENT_PROXY_URL` only.
It never receives `AGENT37_API_URL`, `AGENT37_API_KEY`, or a model key. When that
proxy is unset or does not return `{ source: "agent37", text }`, Aqua answers
from the loaded `agent_context.json`. A separate public Agent37 conversation URL
may still be opened from `VITE_AGENT37_URL`. See `agent/ACCEPTANCE.md`. Live
acceptance stays pending until a real reply from instance `gr7nnwqxgf` is observed.

Scope conflict: MASTER_PLAN.md lists the Agent37 briefing as required and A08
requires live fetch/answer evidence. The user's explicit decision makes this an
optional backup. Local A08 preparation can pass without that service; the original
live checks remain PENDING. The shared plan/contracts are preserved, not silently
rewritten. Do not create an instance or incur charges under this phase.

## Missing prerequisites for optional live activation

- Actual public Agent37 instance URL and access to configure its hosted runtime.
- Runtime support for fresh HTTP/file fetching and schema validation; actual
  authentication/credit entitlement, without sharing private credentials.
- Actual public HTTPS URL serving the complete matching export batch, including
  agent_context.json. Localhost on A's laptop is not reachable from a hosted agent.
- Correct Render workspace confirmation and repository/deployment authorization.
  The connected session has no selected workspace; service state was not guessed.

## Configuration when available

1. Configure the real Agent37 instance with INSTRUCTIONS.md and the existing
   contracts/agent_context.schema.json. Set its actual public context URL in the
   hosted instance configuration. Keep provider credentials inside the platform.
2. Set frontend VITE_AGENT37_URL to the public native conversation URL and
   VITE_AGENT_CONTEXT_URL to the deployed public context JSON URL. Both variables
   are public and bundled at build time. Use HTTPS URLs without credentials,
   query secrets or fragments; no keys/tokens in any VITE_ variable. Rebuild after
   configuration. Leave values empty until the actual URLs are known.
3. Without a deployed URL, the dashboard context-file button checks the local
   /data/agent_context.json only. It validates the existing schema and matching
   metadata/well summaries against the loaded batch. It sends a credential-free
   GET, follows no redirects, times out after eight seconds, and makes no Agent37
   request. Success means context consistency only. Failure never fabricates text.
4. Opening the configured link sends no selected well, method, prompt, export
   values or revealed measurements to the service. Ask the displayed questions
   manually in Agent37. The context uses default_method, even if the chart's
   selected method differs. Do not republish context for a selection change.

## Optional live activation evidence (all PENDING)

Use the real instance and its own tools, never a fabricated response:

| Check | Expected evidence |
| --- | --- |
| Which wells should I inspect first? | Fresh fetch; exported category/change/ID order; at most five wells |
| Explain well &lt;actual selected ID&gt; | Exact summary/method, estimated status and reason; a sensible inspection suggestion |
| What are the limitations? | Historical dates, synthetic/real type, method, assumed physics and field-validation limits |
| Fixture disclosure | Explicit artifact_kind=fixture and no trained result/accuracy claim |
| Fetch failure/timeout | Honest tool/read failure; no successful or cached briefing invented |
| Invalid context | Malformed/schema-invalid data refused; no hidden-observation access |

Compare all answers against the exact deployed batch. Keep actual instance and
tool-fetch evidence locally, without publishing account emails, team codes,
tokens or other private account facts. Until these checks pass, report live A08
acceptance as PENDING / OPTIONAL. This does not gate core functionality or A09.
A09 deployment work needs its own phase authorization.
