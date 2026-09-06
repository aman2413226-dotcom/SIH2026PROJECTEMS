# ❄️ Polar Station AI-Driven Energy Management System (Backend)

An intelligent, mission-critical FastAPI backend designed for isolated Polar Research Stations (Antarctica / Arctic) operating under extreme sub-zero conditions (-50°C to -80°C).

## 🚀 Key Features

- **Battery Energy Storage System (BESS) (`battery.py`)**: Real-time State of Charge (SOC), thermal jacket pre-heating control to prevent battery freeze damage.
- **Master Energy Dashboard (`dashboard.py`)**: Real-time power balance equation:
  $$\text{Wind (kW)} + \text{Solar (kW)} + \text{Diesel (kW)} = \text{Station Load (kW)} + \text{Battery (kW)}$$
- **Polar Diesel Dispatch (`diesel.py`)**: Cold-start safety interlocks (engine block pre-heating check before crank), fuel burn rate, and winter-over supply autonomy tracking.
- **Emissions & Antarctic Treaty (`emission.py`)**: Carbon footprint tracking and Madrid Protocol Annex IV environmental compliance.
- **AI Fault Diagnostics (`faults.py`)**: Detection of turbine blade rime icing, heat-tracing cable current drops, and fuel gelation.
- **AI Forecast Engine (`forecast.py`)**: 24h predictive generation for katabatic wind, polar solar radiation curves, and thermal heating demand.
- **Predictive Maintenance (`maintenance.py`)**: Remaining Useful Life (RUL) estimation and winterization checklists.
- **Digital Twin Simulation (`simulation.py`)**: Multi-day blizzard stress-testing and generator outage simulations.
- **Polar Weather Sensors (`weather.py`)**: Wind chill index calculation, blizzard condition codes, and solar astronomical angles.

---

## 🛠️ Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── battery.py         # BESS & thermal control
│   │   ├── dashboard.py       # Grid balance & KPIs
│   │   ├── diesel.py          # Backup generators & fuel reserves
│   │   ├── emission.py        # Carbon tracking & treaty compliance
│   │   ├── faults.py          # AI fault detection & diagnostics
│   │   ├── forecast.py        # AI predictive forecasting
│   │   ├── maintenance.py     # Winter-over checklists & RUL
│   │   ├── simulation.py      # Digital twin stress test scenarios
│   │   └── weather.py         # Meteorology & wind chill sensors
│   ├── core/                  # Configuration, logging, and security
│   ├── database/              # Database connector placeholder
│   ├── events/                # Async pub/sub event bus and definitions
│   ├── middleware/            # CORS and request telemetry
│   ├── models/                # ORM database models placeholder
│   ├── schemas/               # Pydantic schemas placeholder
│   ├── services/              # Business logic layer
│   ├── tests/                 # Unit and integration tests
│   ├── utils/                 # Shared utilities
│   └── main.py                # Main application entrypoint
├── requirements.txt           # Python dependencies
└── .env.example               # Environment variables
```

---

## 💻 Step-by-Step Instructions: How to Run in VS Code

### 1. Open Terminal in VS Code
In VS Code, press:
- **`Ctrl + \``** (or `Ctrl + ~`), or go to the top menu: **Terminal** > **New Terminal**.

### 2. Navigate to Project Directory
Make sure your terminal is in the project root:
```powershell
cd c:\Users\sanga\OneDrive\Documents\my_project
```

### 3. Create a Python Virtual Environment
Creating a virtual environment ensures dependencies don't conflict with your global Python installation:
```powershell
python -m venv .venv
```

### 4. Activate the Virtual Environment
- **On Windows PowerShell:**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(Note: If PowerShell shows an `Execution_Policies` script error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the command again).*
- **On Command Prompt (cmd.exe):**
  ```cmd
  .venv\Scripts\activate.bat
  ```

Once activated, your terminal prompt will show `(.venv)`.

### 5. Install Dependencies
Install all required packages:
```powershell
pip install -r backend/requirements.txt
```

### 6. Run the FastAPI Server
You can start the server using either method:

**Option A (Using python directly):**
```powershell
python -m backend.app.main
```

**Option B (Using Uvicorn with auto-reload):**
```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 7. Access the Interactive API Docs
Open your web browser and visit:
- **Swagger Interactive UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Alternative UI:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **API Root Check:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
