# PolarEMS: Antarctic Microgrid Digital Twin - Project Study

PolarEMS is a state-of-the-art cyber-physical digital twin and energy management system designed specifically for the extreme conditions of the Bharati Antarctic Research Station. It utilizes real-time telemetry, advanced machine learning, and zero-trust security heuristics to manage a hybrid microgrid (Solar PV, Wind, Battery Storage, and Diesel Generators).

## 🛠️ Technology Stack

### Frontend (Client-Side)
* **Framework:** React / Next.js
* **Styling:** Tailwind CSS (customized for modern industrial SCADA aesthetics)
* **UI/UX Paradigms:** Glassmorphism panels, SVG-based circular gauges, dynamic data flow animations, terminal-style audit logs, full Light/Dark mode support.
* **Icons:** Lucide React

### Backend (Server-Side)
* **Framework:** FastAPI (Python)
* **Data Integration:** Real-time data fetching using Open-Meteo APIs for Bharati Station (-69.4077°S, 76.1872°E) and live NCPOR data.
* **Optimization Engine:** Linear Programming solver (PuLP/SciPy) for dispatch scheduling.

## 🧠 Artificial Intelligence & Machine Learning (AI / ML)

The core intelligence of PolarEMS is driven by specialized machine learning models that forecast renewable generation and station demand to minimize diesel fuel consumption.

* **Algorithm:** LightGBM (Gradient Boosting Framework)
* **Targets Forecasted (24-hour horizon):** 
  1. `load_demand_kw`: Anticipated life support and station operations demand.
  2. `solar_output_kw`: Expected solar photovoltaic generation based on cloud cover and solar irradiance.
  3. `wind_output_kw`: Expected wind turbine generation based on wind speed at 10m/100m.
* **Pipeline:** Automated data ingestion -> Cleaning & Imputation -> Feature Engineering (lag features, rolling averages) -> Model Retraining -> 24-hour Inference.
* **Dispatch Optimization:** The ML forecasts feed directly into a linear programming optimizer (`scheduler.py`) that schedules BESS (Battery Energy Storage System) charging/discharging and diesel generator dispatch. Diesel is only dispatched when the net renewable surplus is negative or the battery SOC drops below critical thresholds (e.g., 22%).

## 🛡️ Cyber-Physical Security & IDS

PolarEMS features a built-in **Cyber-Physical Intrusion Detection System (IDS)** designed to protect critical infrastructure from both digital and physical tampering.

* **Zero-Trust Heuristics Engine:** Continuously monitors grid telemetry vectors for anomalies.
* **Red Team Simulator:** A built-in testing suite that allows operators to inject simulated attacks:
  * **Load Hijack:** Simulates a rogue spike in electrical load.
  * **Sensor Spoof:** Simulates falsified telemetry data from generation nodes.
  * **Thermal Runaway:** Simulates a critical temperature spike in the BESS core.
* **Automated Mitigation:** Upon detecting a threat, the system isolates the compromised subsystem (e.g., overriding rogue loads or shutting down compromised sensors) and updates the security posture to alert operators.
* **Audit Logging:** A terminal-style interface logs all intercepted attacks and operator clearances with precise timestamps.

## 🚀 Future Scalability & Planned Features

As PolarEMS evolves from a prototype to a production-ready system, several key scalability features and enhancements are planned:

### 1. Advanced Security & IDS Scalability
* **Security Score Gauge:** Real-time quantitative assessment of grid resilience.
* **Threat Statistics Row:** Aggregated metrics of intercepted attacks over time.
* **DDoS Attack Vector:** Simulating network-layer attacks on the SCADA telemetry gateway.
* **Audio Alerts:** Critical alarm sounds for compromised states.
* **Relative Timestamps:** Human-readable log times (e.g., "2 mins ago").

### 2. Machine Learning Enhancements
* **Ensemble Modeling:** Combining LightGBM with LSTM networks for better time-series pattern recognition over longer horizons.
* **Predictive Maintenance:** Using historical sensor data (e.g., vibration, temperature) to predict hardware failures in wind turbines or diesel generators before they occur.

### 3. Grid Integration & Expansion
* **Multi-Station Federation:** Scaling the digital twin to manage interconnected microgrids across multiple Antarctic bases (e.g., connecting Bharati and Maitri).
* **Advanced Carbon Tracking:** Granular lifecycle carbon accounting, integrating Scope 1, 2, and 3 emissions for the entire station.

### 4. System Architecture
* **Containerization & Kubernetes:** Deploying the FastAPI backend and ML inference engine across distributed K8s clusters for high availability.
* **WebSockets / gRPC:** Transitioning from REST polling to real-time, low-latency streaming for telemetry and IDS logs.
