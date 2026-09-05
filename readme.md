# PolarEMS — Light Theme (white background replica)

This is a pixel-faithful rebuild of the PolarEMS reference dashboard you
shared — same four tabs, same cards and panels, same metrics — but with
a white/light background instead of dark, using saturated accent colours
(teal, violet, blue, amber, rose) on each card so nothing looks flat or
dull.

## Files

- `index.html` — page structure: topbar, the 5 persistent stat cards,
  and the four tab panels
- `style.css`  — the light visual theme
- `script.js`  — simulation engine, AI classification logic, alarm
  engine, power-flow map, digital-twin controls, and the 24h dispatch
  chart (all hand-built, no external libraries)

## How to run

No install, no build tools, no server required.

1. Put all three files in the same folder.
2. Double-click `index.html` to open it in your browser.

Optional — serve it locally instead of `file://`:
```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## The four tabs (matching the reference)

- **Dashboard** — Microgrid Bus & Power Flow Map (Solar, Wind, Station
  Load / AC Power Bus, BESS Storage, Diesel Genset) plus the Digital
  Twin Playback & Control panel.
- **24h Dispatch** — Run 24h Solver button, expected fuel / emissions /
  cost, and a 24-hour stacked-area chart of solar, wind, battery-assist
  and diesel contribution.
- **Digital Twin** — the same power-flow map and playback controls
  (pause/step/reset, simulation speed, genset online toggle, and a
  station-load injection slider), matching the reference screenshots.
- **Diagnostics & Alarms** — live alarm feed (e.g. wind-turbine rotor
  icing, low battery, low fuel) with alarm codes, plus Rotor Anti-Icing
  and Diesel Service Due status cards.

Every number is driven by one small simulation engine in `script.js` —
weather is switchable from the dropdown next to the clock (clear,
overcast, polar night, calm polar night, blizzard/turbine cutout) so you
can watch the AI outlook, alarms, and dispatch numbers react live.

## Wiring in real hardware

Replace the body of `readSensors()` in `script.js` with a call to your
real telemetry feed, keeping the same return shape
(`solarKw`, `windKw`, `baseLoadKw`, `irradiance`, `tempC`, `windSpeed`,
`turbineCutout`). `state.batterySoc` and `state.fuelLiters` can likewise
be set directly from real sensors instead of being derived by
`stepPower()`.