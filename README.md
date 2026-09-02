# PolarEMS
## AI-Driven Smart Energy Management System for Indian Antarctic Research Stations (Maitri & Bharati)

> Smart India Hackathon (SIH) 2026 Project

---

# Overview
PolarEMS is an AI-powered Energy Management System designed for Indian Antarctic research stations. It combines renewable forecasting, load prediction, battery optimization, intelligent diesel scheduling, simulation, and an event-driven dashboard.

## Objectives
- Reduce diesel consumption
- Maximize renewable utilization
- Optimize battery SOC
- Provide explainable AI recommendations
- Simulate extreme polar scenarios
- Build a digital twin for decision support

# Repository Structure

```text
SIH2026PROJECTEMS/
├── frontend/
├── backend/
├── ai/
├── simulation/
├── optimization/
├── datasets/
├── docs/
├── config/
├── docker/
├── README.md
└── docker-compose.yml
```

## Folder Responsibilities

| Folder | Purpose |
|---|---|
| frontend | Next.js Mission Control dashboard |
| backend | FastAPI APIs and business logic |
| ai | ML models, training and inference |
| simulation | Polar station simulator and digital twin |
| optimization | OR-Tools scheduling engine |
| datasets | Weather, load and synthetic datasets |
| docs | Documentation and project memory |
| config | Shared configuration |

# Technology Stack

## Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion
- Recharts
- Zustand

## Backend
- FastAPI
- Python
- PostgreSQL (future)
- WebSockets (future)
- Docker

## AI
- Pandas
- NumPy
- Scikit-learn
- XGBoost
- LightGBM
- TensorFlow/PyTorch

## Optimization
- Google OR-Tools
- Pyomo

# Development Flow

```text
Research
↓
Frontend
↓
Simulation
↓
Backend
↓
EDA
↓
ML Models
↓
Optimization
↓
Digital Twin
↓
Testing
↓
Deployment
```

# Event Driven Architecture

```text
WeatherUpdated
      ↓
RenewableForecastUpdated
      ↓
LoadForecastUpdated
      ↓
BatteryUpdated
      ↓
OptimizationCompleted
      ↓
RecommendationGenerated
      ↓
TimelineUpdated
      ↓
DashboardUpdated
```

# AI Modules

- Load Forecasting
- Solar Prediction
- Wind Prediction
- Battery SOC Prediction
- Fault Detection
- Predictive Maintenance
- Carbon Estimation

# Optimization

Inputs:
- Load Forecast
- Weather Forecast
- Battery SOC
- Renewable Generation
- Diesel Status

Outputs:
- Charge / Discharge
- Diesel ON/OFF
- Load Shedding
- AI Recommendation

# Simulation Engine

Simulates:
- Weather
- Wind
- Solar
- Battery
- Diesel
- Station Load
- Emergencies
- Blizzard scenarios

# Team Roles

| Role | Responsibilities | Skills |
|---|---|---|
| Project Lead | Architecture, integration, reviews | System Design, Git |
| Frontend Engineer | Dashboard, UI, charts | Next.js, React |
| Backend Engineer | APIs, services, event bus | FastAPI, Python |
| ML Engineer | EDA, forecasting | Pandas, XGBoost |
| Optimization Engineer | Scheduling | OR-Tools |
| Simulation Engineer | Digital Twin | Python, SimPy |

# Working Flow

1. Weather arrives
2. Forecast models execute
3. Load prediction updates
4. Optimization engine runs
5. Recommendation generated
6. Event Bus broadcasts
7. Dashboard refreshes

# Git Workflow

```bash
git pull
git checkout -b feature/<name>
git add .
git commit -m "feat: ..."
git push
```

# Coding Standards

- Modular architecture
- SOLID principles
- No hardcoded values
- Environment variables
- Document every module
- Validate before merge

# Project Memory

Maintain:
- docs/project_memory/project_state.md
- architecture.md
- api_contracts.md
- change_log.md

Every session:
1. Read memory
2. Implement
3. Validate
4. Update memory

# Future Roadmap

- Real Weather APIs
- Live telemetry
- Multi-station support
- Authentication
- Kubernetes deployment
- Explainable AI enhancements

# License

Educational project for Smart India Hackathon 2026.

