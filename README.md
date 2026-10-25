# Aqua Demo — Synthetic Groundwater Station Desk

Interactive three-view demo (Stations, Analysis, Aqua chat) for exploring a synthetic groundwater station export. Every depth and change shown in the interface comes from that export. The measurements are simulated.

## Important

- All data under `frontend/public/data` is synthetic.
- Banner shown in the app: “Simulated groundwater data — not real field measurements.”
- Nothing in the interface or chat represents live sensors, forecasts, or field accuracy.

## Views

- Stations: station list with role, priority, and exported latest depth + 30-day change (when a summary exists).
- Analysis: method comparison over the fixed range 2024-11-02 to 2024-12-31. Map titled “Demonstration region” with OSM attribution. Marker spacing is for display and is not a measured distance.
- Aqua: chat that answers only from the pre-exported synthetic text in `frontend/src/data/assistant.ts`. Follow-up chips are complete questions so they work without conversation history.

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
