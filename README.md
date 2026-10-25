# Aqua Demo — Synthetic Groundwater Station Desk

Interactive three-view demo (Stations, Analysis, Aqua chat) for exploring a synthetic groundwater station export. Every depth and change shown in the interface comes from that export. The measurements are simulated.

## Important

- All data under `frontend/public/data` is synthetic.
- Banner shown in the app: “Simulated groundwater data — not real field measurements.”
- Nothing in the interface or chat represents live sensors, forecasts, or field accuracy.

## Views

- Stations: station list with role, priority, and exported latest depth + 30-day change (when a summary exists). Map titled “Demonstration region” with OSM attribution. Marker spacing is for display and is not a measured distance.
- Analysis: method comparison, outage simulation, and reveal over the fixed range 2024-11-02 to 2024-12-31.
- Aqua: a recorded Agent37 reply can be shown before a new question. New answers come from the export briefing in `frontend/src/data/assistant.ts`. A build with the public proxy shows a live Agent37 reply only when that proxy returns one. If it does not answer, the export briefing stays. Follow-up chips are complete questions and do not send conversation history.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

The frontend expects Node.js 24. From `frontend`, these commands check the export and the app without retraining anything:

```bash
npm run validate:data
npm run typecheck
npm run test
npm run build
```

`npm run validate:data` checks that the four export files agree with each other. It does not certify field accuracy.
