"""
PolarEMS Dashboard & Power Flow API Router
Exposes real-time microgrid energy balance, animated power-flow map coordinates, and KPIs.
"""

from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime, timezone

from simulation.digital_twin import digital_twin

router = APIRouter(prefix="/dashboard", tags=["Station Energy Dashboard"])


@router.get("/overview", summary="Real-Time Station Energy Balance & Status")
async def get_dashboard_overview() -> Dict[str, Any]:
    """
    Returns real-time aggregated microgrid energy balance from the active Digital Twin:
    Wind (kW) + Solar (kW) + Diesel (kW) = Station Load (kW) + BESS Net Flow (kW)
    """
    telemetry = digital_twin.latest_telemetry
    gen = telemetry.get("generation", {})
    pb = telemetry.get("power_balance", {})
    loads = telemetry.get("loads", {})
    bess = telemetry.get("bess", {})
    diesel = telemetry.get("diesel", {})
    env = telemetry.get("environment", {})

    total_gen = pb.get("total_generation_kw", 0.0)
    total_dem = pb.get("total_demand_kw", 0.0)
    renewable_gen = gen.get("renewable_total_kw", 0.0)

    fuel_reserve = diesel.get("fuel_remaining_liters", 45000.0)
    # Estimate projected days based on average ~150-250 L/day
    fuel_burn_h = diesel.get("fuel_burn_rate_l_per_h", 8.5)
    projected_days = round(fuel_reserve / max(10.0, fuel_burn_h * 24.0), 1) if fuel_burn_h > 0 else 180.0

    return {
        "timestamp": telemetry.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "station_name": digital_twin.config["station_name"],
        "station_code": digital_twin.config["station_code"],
        "station_mode": "RESEARCH_LIFE_SUPPORT_ACTIVE",
        "ambient_temperature_c": env.get("ambient_temp_c", -52.4),
        "wind_chill_c": env.get("wind_chill_c", -65.2),
        "environment": env,
        "power_balance": {
            "total_generation_kw": total_gen,
            "total_load_kw": total_dem,
            "net_surplus_kw": pb.get("net_surplus_kw", 0.0),
            "renewable_fraction_pct": pb.get("renewable_penetration_pct", 85.0),
        },
        "generation_sources": {
            "wind_turbines_kw": gen.get("wind_kw", 0.0),
            "solar_pv_kw": gen.get("solar_kw", 0.0),
            "diesel_generators_kw": gen.get("diesel_kw", 0.0),
        },
        "consumption_breakdown": {
            "life_support_heating_kw": loads.get("thermal_heating_kw", 42.0),
            "science_laboratories_kw": loads.get("science_laboratories_kw", 28.5),
            "external_pipe_heat_tracing_kw": loads.get("pipe_heat_tracing_kw", 18.0),
            "base_electrical_kw": loads.get("base_life_support_kw", 48.0),
            "hijacked_cyber_load_kw": loads.get("hijacked_attack_load_kw", 0.0),
            "battery_charging_kw": max(0.0, bess.get("bess_flow_kw", 0.0)),
        },
        "autonomy": {
            "fuel_reserve_liters": round(fuel_reserve, 1),
            "projected_fuel_days": projected_days,
            "battery_soc_pct": bess.get("bess_soc_pct", 75.0),
            "battery_cell_temp_c": bess.get("cell_temp_c", 19.5),
            "battery_backup_hours": round(bess.get("bess_stored_kwh", 350.0) / max(10.0, total_dem), 1),
        },
        "critical_indicators": {
            "grid_frequency_hz": pb.get("grid_frequency_hz", 50.0),
            "grid_voltage_v": pb.get("grid_voltage_v", 400.1),
            "power_factor": 0.98,
            "ice_accumulation_warning": digital_twin.wind.icing_severity > 0.25,
            "turbine_storm_cutout": digital_twin.wind_speed_ms >= digital_twin.wind.cut_out_ms,
        }
    }


@router.get("/power-flow", summary="Live Microgrid Bus & Power Flow Map Data")
async def get_power_flow() -> Dict[str, Any]:
    """
    Supplies real-time node and transfer coordinates for the interactive animated power-flow visualization.
    Shows flow magnitude and direction from Solar/Wind/Diesel into AC Central Bus,
    and from AC Bus into BESS Storage and Life-Support Loads.
    """
    telemetry = digital_twin.latest_telemetry
    gen = telemetry.get("generation", {})
    bess = telemetry.get("bess", {})
    pb = telemetry.get("power_balance", {})
    loads = telemetry.get("loads", {})

    bess_flow = bess.get("bess_flow_kw", 0.0)  # positive = charging, negative = discharging

    return {
        "timestamp": telemetry.get("timestamp"),
        "station": digital_twin.config["station_code"],
        "nodes": {
            "solar": {
                "id": "solar",
                "label": "Solar PV Arrays",
                "type": "GENERATOR",
                "current_kw": gen.get("solar_kw", 0.0),
                "is_active": gen.get("solar_kw", 0.0) > 0.1,
                "status": "ONLINE" if gen.get("solar_kw", 0.0) > 0.1 else "POLAR_NIGHT_OFFLINE",
            },
            "wind": {
                "id": "wind",
                "label": "Wind Turbines",
                "type": "GENERATOR",
                "current_kw": gen.get("wind_kw", 0.0),
                "is_active": gen.get("wind_kw", 0.0) > 0.1,
                "status": "CUTOUT" if digital_twin.wind_speed_ms >= 25.0 else ("ICED" if digital_twin.wind.icing_severity > 0.3 else "ONLINE"),
            },
            "diesel": {
                "id": "diesel",
                "label": "Diesel Powerhouse",
                "type": "GENERATOR",
                "current_kw": gen.get("diesel_kw", 0.0),
                "is_active": gen.get("diesel_kw", 0.0) > 0.1,
                "status": "ONLINE" if gen.get("diesel_kw", 0.0) > 0.1 else "STANDBY",
            },
            "central_bus": {
                "id": "central_bus",
                "label": "AC Microgrid Bus (400V 50Hz)",
                "type": "BUS",
                "frequency_hz": pb.get("grid_frequency_hz", 50.0),
                "total_flow_kw": pb.get("total_generation_kw", 0.0),
            },
            "bess": {
                "id": "bess",
                "label": "BESS Storage",
                "type": "STORAGE",
                "soc_pct": bess.get("bess_soc_pct", 75.0),
                "flow_kw": bess_flow,
                "state": "CHARGING" if bess_flow > 0.1 else ("DISCHARGING" if bess_flow < -0.1 else "IDLE"),
                "cell_temp_c": bess.get("cell_temp_c", 19.5),
            },
            "station_loads": {
                "id": "station_loads",
                "label": "Station Habitat & Science Loads",
                "type": "CONSUMER",
                "total_demand_kw": pb.get("total_demand_kw", 75.0),
                "thermal_heating_kw": loads.get("thermal_heating_kw", 35.0),
                "life_support_intact": True,
            }
        },
        "flows": [
            {"from": "solar", "to": "central_bus", "kw": gen.get("solar_kw", 0.0), "direction": "FORWARD"},
            {"from": "wind", "to": "central_bus", "kw": gen.get("wind_kw", 0.0), "direction": "FORWARD"},
            {"from": "diesel", "to": "central_bus", "kw": gen.get("diesel_kw", 0.0), "direction": "FORWARD"},
            {
                "from": "central_bus",
                "to": "bess",
                "kw": abs(bess_flow),
                "direction": "FORWARD" if bess_flow > 0 else "REVERSE",  # FORWARD = bus to batt, REVERSE = batt to bus
            },
            {"from": "central_bus", "to": "station_loads", "kw": pb.get("total_demand_kw", 75.0), "direction": "FORWARD"},
        ]
    }


@router.get("/kpi", summary="Key Performance Indicators (Last 24 Hours)")
async def get_dashboard_kpi() -> Dict[str, Any]:
    """Provides key performance indices for polar microgrid efficiency and sustainability."""
    telemetry = digital_twin.latest_telemetry
    diesel = telemetry.get("diesel", {})
    pb = telemetry.get("power_balance", {})

    total_liters = diesel.get("cumulative_fuel_liters", 4120.0)
    co2_tonnes = diesel.get("cumulative_co2_tonnes", 11.04)

    return {
        "period": "Last 24 Hours Rolling",
        "station": digital_twin.config["station_name"],
        "total_energy_consumed_kwh": round(digital_twin.cumulative_renewable_kwh + (total_liters * 3.5), 1),
        "renewable_energy_generated_kwh": round(digital_twin.cumulative_renewable_kwh, 1),
        "renewable_penetration_average_pct": pb.get("renewable_penetration_pct", 78.5),
        "diesel_fuel_consumed_liters": round(total_liters, 1),
        "diesel_fuel_saved_by_renewables_liters": round(digital_twin.cumulative_renewable_kwh / 3.4, 1),
        "co2_emissions_avoided_tonnes": round((digital_twin.cumulative_renewable_kwh / 3.4) * 2.68 / 1000.0, 2),
        "co2_emissions_cumulative_tonnes": co2_tonnes,
        "peak_station_demand_kw": 124.5,
        "min_station_demand_kw": 62.0,
    }
