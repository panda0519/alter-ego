# Official and primary sources checked on 21 October 2026

These links support tool/event/data facts. Architecture, defaults, time allocations and
spending caps are our engineering choices, not promises made by these sources.

| Topic | Source |
|---|---|
| Event prizes | https://hackyard.org/build2026/prizes |
| Event rules and disclosure | https://hackyard.org/build2026/rules |
| Updated event timetable | https://hackyard.org/build2026/timeline |
| Agent37 qualification evidence | https://hackyard.org/build2026/agent37 |
| Codex IDE setup | https://developers.openai.com/codex/ide/ |
| Codex project instructions | https://developers.openai.com/codex/guides/agents-md/ |
| Cursor AGENTS.md and rules | https://cursor.com/docs/rules |
| Node download | https://nodejs.org/en/download |
| Vite setup/runtime | https://vite.dev/guide/ |
| PyTorch CUDA/CPU wheels | https://pytorch.org/get-started/previous-versions/ |
| Python Windows installer baseline | https://www.python.org/downloads/release/python-3119/ |
| Render static hosting | https://render.com/docs/static-sites |
| Nodus platform | https://nodus-platform-site.pages.dev/ |
| Nodus jobs quickstart | https://nodus-platform-site.pages.dev/docs/getting-started/ |
| Nodus coding-agent integration | https://nodus-platform-site.pages.dev/docs/guides/mcp/ |
| Nodus workspace fallback | https://nodus-platform-site.pages.dev/docs/guides/workspaces/ |
| Agent37 current capabilities/plans | https://www.agent37.com/personal |
| India-WRIS source portal | https://indiawris.gov.in/wris/#/timeseriesdata |
| Alternative telemetry listing | https://ckandev.indiadataportal.com/dataset/groundwater-level/resource/f78f7b15-f325-4c39-a291-f44ad4e95334 |
| NASA POWER daily API | https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| NASA spatial resolution guidance | https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/ |
| Hargreaves equation and units, FAO Eq. 52 | https://www.fao.org/4/x0490e/x0490e07.htm |

The India-WRIS direct portal timed out during the earlier check. A telemetry listing and
its download option were found, but neither a suitable real subset nor its usage rights
have been established by this pack. No actual groundwater data were downloaded here.
Frontend direct versions were read from the npm registry and a package lock was resolved;
the actual app still needs npm ci and a build on A's machine. Selected TypeScript 5.9.3 stays on the established
5.x toolchain rather than adopting a new compiler major for the event.
