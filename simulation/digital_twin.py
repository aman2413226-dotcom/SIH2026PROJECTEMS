"""
PolarEMS High-Fidelity Digital Twin State Machine & Engine
Coordinates real-time physics, meteorological feeds, faults, and cyber-attacks.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import math
import random

from config.station_config import get_station_config, DEFAULT_STATION
from config.constants import calculate_wind_chill, DIESEL_CO2_KG_PER_LITER
from simulation.engine.simulator import (
    SolarArrayModel,
    WindTurbineSystem,
    DieselGensetCluster,
    BatteryStorageSystem,
)


class DigitalTwinEngine:
    """
    Industrial Digital Twin Engine for Polar Microgrids.
    Controls simulation time, physics iteration, fault injection, and telemetry.
    """

    def __init__(self, station_name: str = DEFAULT_STATION):
        self.station_key = station_name.upper()
        self.config = get_station_config(self.station_key)
        specs = self.config["grid_specs"]

        # Time controls
        self.sim_time = datetime.now(timezone.utc)
        self.is_running = True
        self.speed_multiplier = 1  # 1x, 2x, 5x, 10x, 50x

        # Physics sub-models
        self.solar = SolarArrayModel(
            capacity_kw=specs["solar_pv_capacity_kw"],
            latitude=self.config["latitude"],
            albedo_factor=specs["bifacial_albedo_factor"],
        )
        self.wind = WindTurbineSystem(
            capacity_kw=specs["wind_turbine_capacity_kw"],
            cut_in_ms=specs["wind_cut_in_ms"],
            rated_ms=specs["wind_rated_ms"],
            cut_out_ms=specs["wind_cut_out_ms"],
        )
        self.diesel = DieselGensetCluster(
            count=specs["diesel_genset_count"],
            rated_kw=specs["diesel_genset_rated_kw"],
            tank_capacity_liters=specs["diesel_fuel_tank_liters"],
            fuel_rate_l_per_kwh=specs["fuel_consumption_rate_l_per_kwh"],
            idle_fuel_rate_l_per_h=specs["genset_idle_fuel_rate_l_per_h"],
            min_runtime_hours=specs["genset_min_runtime_hours"],
        )
        self.bess = BatteryStorageSystem(
            capacity_kwh=specs["bess_capacity_kwh"],
            nominal_charge_kw=specs["bess_nominal_charge_kw"],
            nominal_discharge_kw=specs["bess_nominal_discharge_kw"],
            initial_soc_pct=78.5,
        )

        # Environmental conditions (can be updated from live NCPOR feed or simulation)
        self.ambient_temp_c = -52.4
        self.wind_speed_ms = 14.8
        self.cloud_cover = 0.15
        self.atmospheric_pressure_hpa = 645.0
        self.relative_humidity_pct = 28.0

        # Station electrical loads
        self.manual_load_override: Optional[float] = None
        self.base_electrical_load_kw = specs["base_electrical_load_kw"]
        self.thermal_conductance = specs["thermal_conductance_kw_per_c"]
        self.target_indoor_temp_c = specs["target_indoor_temp_c"]

        # Cumulative statistics
        self.cumulative_diesel_liters = 4120.0
        self.cumulative_co2_tonnes = round(self.cumulative_diesel_liters * DIESEL_CO2_KG_PER_LITER / 1000.0, 2)
        self.cumulative_renewable_kwh = 18450.0

        # Active Faults and Injections
        self.active_faults: Dict[str, Dict[str, Any]] = {}
        self.sensor_freeze_active = False
        self.frozen_telemetry: Dict[str, Any] = {}

        # Red Team cyber-attack flags
        self.hijacked_load_kw = 0.0
        self.spoofed_sensor_data: Optional[Dict[str, float]] = None

        # Telemetry cache
        self.latest_telemetry: Dict[str, Any] = {}
        self.tick(seconds=1)

    def set_station(self, station_name: str):
        """Switches station configuration between Maitri and Bharati."""
        self.station_key = station_name.upper()
        self.config = get_station_config(self.station_key)
        specs = self.config["grid_specs"]
        self.solar.capacity_kw = specs["solar_pv_capacity_kw"]
        self.solar.latitude = self.config["latitude"]
        self.wind.capacity_kw = specs["wind_turbine_capacity_kw"]
        self.diesel.rated_kw = specs["diesel_genset_rated_kw"]
        self.bess.capacity_kwh = specs["bess_capacity_kwh"]
        self.base_electrical_load_kw = specs["base_electrical_load_kw"]
        self.thermal_conductance = specs["thermal_conductance_kw_per_c"]

    def set_speed(self, multiplier: int):
        self.speed_multiplier = max(1, min(100, multiplier))

    def play(self):
        self.is_running = True

    def pause(self):
        self.is_running = False

    def reset(self):
        """Resets simulation time and clears transient faults/attacks."""
        self.sim_time = datetime.now(timezone.utc)
        self.is_running = True
        self.speed_multiplier = 1
        self.active_faults.clear()
        self.sensor_freeze_active = False
        self.frozen_telemetry.clear()
        self.hijacked_load_kw = 0.0
        self.spoofed_sensor_data = None
        self.manual_load_override = None
        self.bess.soc_pct = 78.5
        self.bess.cell_temp_c = 19.5
        self.diesel.gensets[0]["status"] = "ONLINE"
        self.diesel.gensets[1]["status"] = "STANDBY"
        self.diesel.gensets[2]["status"] = "STANDBY"
        self.wind.icing_severity = 0.0
        self.tick(seconds=1)

    def inject_fault(self, fault_type: str) -> Dict[str, Any]:
        """Injects a real-world physical polar microgrid fault."""
        fault_id = f"FLT-{random.randint(1000, 9999)}"
        timestamp = self.sim_time.isoformat()

        if fault_type == "BLIZZARD":
            self.wind_speed_ms = 32.5  # Exceeds 25 m/s cutout
            self.ambient_temp_c = -68.0
            self.cloud_cover = 1.0
            fault_record = {
                "fault_id": fault_id,
                "timestamp": timestamp,
                "system": "Atmospheric / Wind Farm",
                "severity": "CRITICAL",
                "fault_type": "CATASTROPHIC_BLIZZARD",
                "ai_confidence_score": 0.99,
                "description": "Category 5 Katabatic blizzard: Sustained winds at 32.5 m/s. Wind turbines auto-feathered. Exterior heat loss doubled.",
                "ai_recommendation": "Activate secondary diesel generator; lock battery for habitat heating life support only.",
                "acknowledged": False,
            }
        elif fault_type == "ICING":
            self.wind.icing_severity = 0.85
            fault_record = {
                "fault_id": fault_id,
                "timestamp": timestamp,
                "system": "Wind Turbine #1 & #2",
                "severity": "WARNING",
                "fault_type": "HEAVY_ROTOR_RIME_ICING",
                "ai_confidence_score": 0.95,
                "description": "Heavy rime ice detected on turbine blades, aerodynamic power reduced by 42%.",
                "ai_recommendation": "Engage blade anti-icing heating elements and adjust pitch angle.",
                "acknowledged": False,
            }
        elif fault_type == "GEN_TRIP":
            self.diesel.gensets[0]["status"] = "FAULT_TRIPPED"
            self.diesel.gensets[0]["output_kw"] = 0.0
            # Genset 2 begins warming up
            self.diesel.gensets[1]["status"] = "WARMING_UP"
            self.diesel.gensets[1]["startup_timer_s"] = 120.0
            fault_record = {
                "fault_id": fault_id,
                "timestamp": timestamp,
                "system": "Diesel Powerhouse GEN-01",
                "severity": "CRITICAL",
                "fault_type": "PRIMARY_GENSET_UNDER_LOAD_TRIP",
                "ai_confidence_score": 0.98,
                "description": "Primary Genset 1 tripped on overcurrent alarm under 80 kW load. BESS absorbing transient deficit.",
                "ai_recommendation": "Genset 2 pre-heat initiated. Transfer critical bus to BESS for 120 seconds.",
                "acknowledged": False,
            }
        elif fault_type == "SENSOR_FREEZE":
            self.sensor_freeze_active = True
            self.frozen_telemetry = {
                "ambient_temp_c": self.ambient_temp_c,
                "wind_speed_ms": self.wind_speed_ms,
            }
            fault_record = {
                "fault_id": fault_id,
                "timestamp": timestamp,
                "system": "AWS Meteorological Mast",
                "severity": "WARNING",
                "fault_type": "ULTRASONIC_ANEMOMETER_FREEZE",
                "ai_confidence_score": 0.92,
                "description": "Temperature and wind speed values frozen. Heated cup anemometer heater fault detected.",
                "ai_recommendation": "Switch meteorological feed to backup mast AWS-B.",
                "acknowledged": False,
            }
        else:
            fault_record = {
                "fault_id": fault_id,
                "timestamp": timestamp,
                "system": "General Microgrid",
                "severity": "INFO",
                "fault_type": fault_type,
                "ai_confidence_score": 0.85,
                "description": f"Generic fault simulation event: {fault_type}",
                "ai_recommendation": "Monitor telemetry.",
                "acknowledged": False,
            }

        self.active_faults[fault_id] = fault_record
        return fault_record

    def clear_fault(self, fault_id: str) -> bool:
        """Clears an active fault and restores normal physical baseline."""
        if fault_id in self.active_faults:
            fault = self.active_faults.pop(fault_id)
            if fault["fault_type"] == "CATASTROPHIC_BLIZZARD":
                self.wind_speed_ms = 14.5
                self.ambient_temp_c = -52.4
                self.cloud_cover = 0.15
            elif fault["fault_type"] == "HEAVY_ROTOR_RIME_ICING":
                self.wind.icing_severity = 0.0
            elif fault["fault_type"] == "PRIMARY_GENSET_UNDER_LOAD_TRIP":
                self.diesel.gensets[0]["status"] = "ONLINE"
            elif fault["fault_type"] == "ULTRASONIC_ANEMOMETER_FREEZE":
                self.sensor_freeze_active = False
                self.frozen_telemetry.clear()
            return True
        return False

    def tick(self, seconds: float = 1.0) -> Dict[str, Any]:
        """
        Main physics tick advancing the simulation by `seconds * speed_multiplier`.
        Computes generation, demand, BESS flows, diesel dispatch, emissions, and grid health.
        """
        effective_seconds = seconds * self.speed_multiplier if self.is_running else 0.0
        dt_hours = effective_seconds / 3600.0

        # Advance simulation clock
        self.sim_time += timedelta(seconds=effective_seconds)
        doy = self.sim_time.timetuple().tm_yday
        hour_utc = self.sim_time.hour + (self.sim_time.minute / 60.0) + (self.sim_time.second / 3600.0)

        # Weather dynamics with gentle polar micro-variation
        if not self.sensor_freeze_active:
            temp_jitter = (math.sin(hour_utc * 0.26) * 0.05)
            self.ambient_temp_c = round(self.ambient_temp_c + temp_jitter, 2)
            wind_jitter = (random.random() - 0.5) * 0.15
            self.wind_speed_ms = max(0.5, round(self.wind_speed_ms + wind_jitter, 2))

        wind_chill_c = calculate_wind_chill(self.ambient_temp_c, self.wind_speed_ms)

        # 1. Renewable Generation Physics
        solar_data = self.solar.compute_power(day_of_year=doy, hour_utc=hour_utc, cloud_cover=self.cloud_cover)
        solar_kw = solar_data["solar_kw"]

        wind_data = self.wind.step(
            wind_speed_ms=self.wind_speed_ms,
            ambient_temp_c=self.ambient_temp_c,
            dt_hours=max(0.001, dt_hours),
        )
        wind_kw = wind_data["wind_kw"]
        renewable_total_kw = round(solar_kw + wind_kw, 1)

        # 2. Station Demand Physics
        # Dynamic thermal heating load scales with difference between indoor (+21°C) and exterior wind chill
        subzero_delta = max(0.0, self.target_indoor_temp_c - wind_chill_c)
        thermal_heating_kw = round(subzero_delta * self.thermal_conductance, 1)

        scientific_load_kw = 28.5
        heat_tracing_cables_kw = 18.0
        base_electrical = self.base_electrical_load_kw + scientific_load_kw + heat_tracing_cables_kw

        nominal_demand = round(base_electrical + thermal_heating_kw, 1)

        # Apply manual load injection or hijacked cyber-attack load
        total_demand_kw = nominal_demand
        if self.manual_load_override is not None:
            total_demand_kw = self.manual_load_override + thermal_heating_kw

        if self.hijacked_load_kw > 0.0:
            total_demand_kw += self.hijacked_load_kw

        total_demand_kw = round(total_demand_kw, 1)

        # 3. Microgrid Energy Dispatch (Renewables -> BESS / Diesel -> Load)
        net_renewable_surplus = renewable_total_kw - total_demand_kw

        # Check if diesel is needed
        diesel_required_kw = 0.0
        if net_renewable_surplus < 0:
            deficit_kw = abs(net_renewable_surplus)
            # Check if BESS can supply deficit or if diesel must carry
            rate_factor = self.bess.soc_pct / 100.0
            if self.bess.soc_pct <= 22.0:
                diesel_required_kw = deficit_kw
            else:
                # BESS covers deficit up to nominal discharge rate
                max_bess_discharge = self.bess.nominal_discharge_kw
                if deficit_kw > max_bess_discharge:
                    diesel_required_kw = deficit_kw - max_bess_discharge

        diesel_data = self.diesel.dispatch(diesel_required_kw, max(0.0001, dt_hours))
        diesel_kw = diesel_data["total_diesel_kw"]

        # Net balance into BESS
        bess_net_input_kw = (renewable_total_kw + diesel_kw) - total_demand_kw
        bess_data = self.bess.step(
            net_power_kw=bess_net_input_kw,
            ambient_temp_c=self.ambient_temp_c,
            dt_hours=max(0.0001, dt_hours),
        )

        total_generation_kw = round(renewable_total_kw + diesel_kw, 1)

        # Cumulative totals
        self.cumulative_diesel_liters += diesel_data["fuel_consumed_liters"]
        self.cumulative_co2_tonnes = round(self.cumulative_diesel_liters * DIESEL_CO2_KG_PER_LITER / 1000.0, 3)
        self.cumulative_renewable_kwh += round(renewable_total_kw * dt_hours, 2)

        # Grid frequency & voltage stability under load
        freq_dev = (total_generation_kw - total_demand_kw) * 0.002
        grid_freq_hz = round(50.0 + max(-0.25, min(0.25, freq_dev)), 2)

        penetration_pct = 100.0
        if total_generation_kw > 0:
            penetration_pct = round((renewable_total_kw / total_generation_kw) * 100.0, 1)

        # Build comprehensive telemetry
        self.latest_telemetry = {
            "timestamp": self.sim_time.isoformat(),
            "station_code": self.config["station_code"],
            "station_name": self.config["station_name"],
            "operator": self.config["operator"],
            "simulation": {
                "is_running": self.is_running,
                "speed_multiplier": self.speed_multiplier,
                "active_faults_count": len(self.active_faults),
            },
            "environment": {
                "ambient_temp_c": self.ambient_temp_c,
                "wind_chill_c": wind_chill_c,
                "wind_speed_ms": self.wind_speed_ms,
                "wind_direction_compass": "SSW (Katabatic Slope Flow)",
                "atmospheric_pressure_hpa": self.atmospheric_pressure_hpa,
                "relative_humidity_pct": self.relative_humidity_pct,
                "solar_elevation_deg": solar_data["solar_elevation_deg"],
                "ghi_wm2": solar_data["ghi_wm2"],
            },
            "power_balance": {
                "total_generation_kw": total_generation_kw,
                "total_demand_kw": total_demand_kw,
                "net_surplus_kw": round(total_generation_kw - total_demand_kw, 1),
                "renewable_penetration_pct": penetration_pct,
                "grid_frequency_hz": grid_freq_hz,
                "grid_voltage_v": 400.1,
            },
            "generation": {
                "solar_kw": solar_kw,
                "wind_kw": wind_kw,
                "diesel_kw": diesel_kw,
                "renewable_total_kw": renewable_total_kw,
            },
            "loads": {
                "base_life_support_kw": round(self.base_electrical_load_kw, 1),
                "thermal_heating_kw": thermal_heating_kw,
                "science_laboratories_kw": scientific_load_kw,
                "pipe_heat_tracing_kw": heat_tracing_cables_kw,
                "hijacked_attack_load_kw": self.hijacked_load_kw,
                "manual_injected_load_kw": self.manual_load_override or 0.0,
            },
            "bess": bess_data,
            "diesel": {
                "gensets": diesel_data["gensets"],
                "fuel_remaining_liters": diesel_data["fuel_remaining_liters"],
                "fuel_burn_rate_l_per_h": round(diesel_data["fuel_consumed_liters"] / max(0.0001, dt_hours), 2) if dt_hours > 0 else 0.0,
                "co2_rate_kg_per_h": round((diesel_kw * 0.28 * DIESEL_CO2_KG_PER_LITER), 2),
                "cumulative_fuel_liters": round(self.cumulative_diesel_liters, 1),
                "cumulative_co2_tonnes": self.cumulative_co2_tonnes,
            },
            "active_faults": list(self.active_faults.values()),
        }

        return self.latest_telemetry


# Singleton Digital Twin Instance for application-wide access
digital_twin = DigitalTwinEngine()
