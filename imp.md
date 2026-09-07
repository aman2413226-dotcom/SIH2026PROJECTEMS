# Important Project Instructions (imp.md)

## Starting the Project

To run both the backend and frontend simultaneously without manually typing out the commands, run the following script from the root of the project:

```bash
.\start.bat
```

This will open two separate command prompt windows:
1. **Backend Server**
2. **Frontend Server**

To stop the servers, simply close the two command prompt windows.

---

## Important Rules

As requested, the project must **NEVER** generate the following files or directories:
- `node_modules/`
- `.next/`
- `__pycache__/`

### How this is enforced:
1. The AI Assistant has strict memory rules not to run `npm install`, `npm run dev`, or `python` commands that create these files.
2. The `start.bat` script uses the `python -B` flag which explicitly tells Python to **not** write `.pyc` files or generate a `__pycache__` folder on your disk.

---

## Manual Start Commands

If you ever need to start them manually from the root directory (`SIH2026PROJECTEMS`):

**Start Backend (No Cache):**
```bash
python -B -m backend.app.main
```

**Start Frontend:**
```bash
cd frontend
npm run dev
```

---

## Future Scalability Features (IDS Improvements — Saved for Later)

1. **Security Score Gauge** — Animated circular SVG gauge (100 → 20) with color transitions
2. **Threat Statistics Row** — 4 mini cards: Total Intercepted, Active Threats, MTTD (< 50ms), Uptime Since Last Breach
3. **New Attack Vector: DDoS / Modbus Protocol Flood** — 4th Red Team attack simulating SCADA gateway flooding
4. **Relative Timestamps** — Audit log entries show "2s ago", "15s ago" instead of raw UTC
5. **Audio Alert on COMPROMISED** — Browser beep/siren on posture transition with toggle switch

