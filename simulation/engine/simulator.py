"""
PolarEMS Physics-Based Microgrid Simulator Components
"""

import math
from typing import Dict, Any, List
from config.constants import (
    get_capacity_factor,
    get_rate_factor,
    calculate_wind_chill,
    DIESEL_CO2_KG_PER_LITER,
    DIESEL_NOX_G_PER_LITER,
    DIESEL_PM_G_PER_LITER,
)
from config.station_config import get_station_config


class SolarArrayModel:
    """Physics model of Antarctic bifacial solar PV array."""

    def __init__(self, capacity_kw: float, latitude: float, albedo_factor: float = 1.25):
        self.capacity_kw = capacity_kw
        self.latitude = latitude
        self.albedo_factor = albedo_factor

    def compute_power(self, day_of_year: int, hour_utc: float, cloud_cover: float = 0.1) -> Dict[str, float]:
        """
        Computes solar PV output based on solar declination, hour angle, and polar ground snow albedo.
        In austral summer (Nov-Feb), continuous 24h sunlight (Midnight Sun).
        In austral winter (May-Aug), zero sunlight (Polar Night).
        """
        # Solar declination angle delta (approx Cooper's equation)
        declination = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
        lat_rad = math.radians(self.latitude)
        dec_rad = math.radians(declination)

        # Hour angle (15 deg per hour from solar noon ~ 12:00)
        hour_angle = (hour_utc - 12.0) * 15.0
        ha_rad = math.radians(hour_angle)

        # Solar elevation angle (sin alpha = sin phi * sin delta + cos phi * cos delta * cos omega)
        sin_elev = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad)
        elevation_deg = math.degrees(math.asin(max(-1.0, min(1.0, sin_elev))))

        if elevation_deg <= 0.0:
            return {
                "solar_kw": 0.0,
                "solar_elevation_deg": round(elevation_deg, 1),
                "ghi_wm2": 0.0,
                "albedo_boost_pct": 0.0,
            }

        # Clear sky irradiance estimate at high polar elevation
        clearness = 1.0 - (cloud_cover * 0.75)
        # Low air mass, high reflection from Antarctic ice sheet
        ghi = round(1050.0 * (elevation_deg / 45.0) ** 0.85 * clearness, 1)
        ghi = max(0.0, min(1100.0, ghi))

        # Bifacial PV gain from snow cover
        effective_capacity = self.capacity_kw * (self.albedo_factor if elevation_deg > 3.0 else 1.0)
        power_kw = round((ghi / 1000.0) * effective_capacity * 0.88, 1)
        power_kw = max(0.0, min(self.capacity_kw * 1.15, power_kw))

        return {
            "solar_kw": power_kw,
            "solar_elevation_deg": round(elevation_deg, 1),
            "ghi_wm2": ghi,
            "albedo_boost_pct": round((self.albedo_factor - 1.0) * 100, 1),
        }


class WindTurbineSystem:
    """Physics model of Antarctic Katabatic Wind Turbines."""

    def __init__(self, capacity_kw: float, cut_in_ms: float = 3.0, rated_ms: float = 12.0, cut_out_ms: float = 25.0):
        self.capacity_kw = capacity_kw
        self.cut_in_ms = cut_in_ms
        self.rated_ms = rated_ms
        self.cut_out_ms = cut_out_ms
        self.icing_severity = 0.0  # 0.0 (clean) to 1.0 (heavy riming)
        self.deicing_heater_active = False

    def step(self, wind_speed_ms: float, ambient_temp_c: float, dt_hours: float) -> Dict[str, Any]:
        """Calculates wind generation accounting for storm cut-off and blade icing."""
        # Check icing accumulation conditions: high humidity/sub-zero
        if ambient_temp_c < -5.0 and ambient_temp_c > -25.0 and not self.deicing_heater_active:
            self.icing_severity = min(1.0, self.icing_severity + 0.04 * dt_hours)
        elif self.deicing_heater_active:
            self.icing_severity = max(0.0, self.icing_severity - 0.25 * dt_hours)

        # Storm cutout check (Katabatic storm exceeding safety threshold)
        if wind_speed_ms >= self.cut_out_ms:
            return {
                "wind_kw": 0.0,
                "turbine_status": "STORM_CUTOUT_FEATHERED",
                "icing_pct": round(self.icing_severity * 100, 1),
                "deicing_heater_active": self.deicing_heater_active,
                "deicing_heater_draw_kw": 4.0 if self.deicing_heater_active else 0.0,
            }

        if wind_speed_ms < self.cut_in_ms:
            return {
                "wind_kw": 0.0,
                "turbine_status": "CALM_BELOW_CUTIN",
                "icing_pct": round(self.icing_severity * 100, 1),
                "deicing_heater_active": self.deicing_heater_active,
                "deicing_heater_draw_kw": 0.0,
            }

        # Cubic power curve up to rated speed, then capped at rated capacity
        if wind_speed_ms >= self.rated_ms:
            raw_power = self.capacity_kw
        else:
            speed_ratio = (wind_speed_ms - self.cut_in_ms) / (self.rated_ms - self.cut_in_ms)
            raw_power = self.capacity_kw * (speed_ratio ** 2.7)

        # Icing causes aerodynamic penalty up to 45%
        icing_penalty = 1.0 - (self.icing_severity * 0.45)
        power_kw = round(max(0.0, min(self.capacity_kw, raw_power * icing_penalty)), 1)

        status = "OPTIMAL_GENERATION"
        if self.icing_severity > 0.3:
            status = "ICING_DERATED"

        return {
            "wind_kw": power_kw,
            "turbine_status": status,
            "icing_pct": round(self.icing_severity * 100, 1),
            "deicing_heater_active": self.deicing_heater_active,
            "deicing_heater_draw_kw": 4.0 if self.deicing_heater_active else 0.0,
        }


class DieselGensetCluster:
    """Multi-generator diesel powerplant with startup delay & anti-short-cycling."""

    def __init__(
        self,
        count: int = 3,
        rated_kw: float = 80.0,
        tank_capacity_liters: float = 50000.0,
        fuel_rate_l_per_kwh: float = 0.28,
        idle_fuel_rate_l_per_h: float = 2.8,
        min_runtime_hours: float = 3.0,
    ):
        self.count = count
        self.rated_kw = rated_kw
        self.tank_capacity_liters = tank_capacity_liters
        self.fuel_remaining_liters = tank_capacity_liters * 0.82  # ~82% full at start
        self.fuel_rate_l_per_kwh = fuel_rate_l_per_kwh
        self.idle_fuel_rate_l_per_h = idle_fuel_rate_l_per_h
        self.min_runtime_hours = min_runtime_hours

        # Per-genset states
        self.gensets = [
            {
                "id": f"GEN-0{i+1}",
                "name": f"Genset #{i+1} ({rated_kw} kW)",
                "status": "ONLINE" if i == 0 else "STANDBY",
                "output_kw": 0.0,
                "runtime_hours": 3420.0 + (i * 450.0),
                "hours_since_started": 1.5 if i == 0 else 0.0,
                "maintenance_due_hours": 500.0 - ((3420.0 + i * 450.0) % 500.0),
                "coolant_temp_c": 82.0 if i == 0 else 45.0,
                "startup_timer_s": 0.0,
            }
            for i in range(count)
        ]

    def dispatch(self, required_kw: float, dt_hours: float) -> Dict[str, Any]:
        """Dispatches gensets to satisfy required_kw while obeying min runtime."""
        active_kw = 0.0
        fuel_consumed = 0.0

        for g in self.gensets:
            if g["status"] == "ONLINE":
                g["hours_since_started"] += dt_hours
                g["runtime_hours"] += dt_hours
                g["maintenance_due_hours"] = max(0.0, g["maintenance_due_hours"] - dt_hours)
                g["coolant_temp_c"] = 85.0

                # Assign load
                allotment = min(self.rated_kw, max(0.0, required_kw - active_kw))
                g["output_kw"] = round(allotment, 1)
                active_kw += allotment

                # Fuel: idle burn + variable load burn
                if allotment > 0.0:
                    fuel_step = (allotment * self.fuel_rate_l_per_kwh + self.idle_fuel_rate_l_per_h) * dt_hours
                else:
                    fuel_step = self.idle_fuel_rate_l_per_h * dt_hours
                fuel_consumed += fuel_step

            elif g["status"] == "WARMING_UP":
                g["startup_timer_s"] -= dt_hours * 3600
                if g["startup_timer_s"] <= 0:
                    g["status"] = "ONLINE"
                    g["hours_since_started"] = 0.0
                g["output_kw"] = 0.0
                fuel_consumed += (self.idle_fuel_rate_l_per_h * 0.5) * dt_hours
            else:
                g["output_kw"] = 0.0

        self.fuel_remaining_liters = max(0.0, self.fuel_remaining_liters - fuel_consumed)
        co2_kg = fuel_consumed * DIESEL_CO2_KG_PER_LITER

        return {
            "total_diesel_kw": round(active_kw, 1),
            "fuel_consumed_liters": round(fuel_consumed, 3),
            "fuel_remaining_liters": round(self.fuel_remaining_liters, 1),
            "co2_emitted_kg": round(co2_kg, 2),
            "gensets": self.gensets,
        }


class BatteryStorageSystem:
    """Polar Battery Energy Storage System (BESS) with cold-derating physics."""

    def __init__(
        self,
        capacity_kwh: float = 500.0,
        nominal_charge_kw: float = 100.0,
        nominal_discharge_kw: float = 100.0,
        initial_soc_pct: float = 78.0,
    ):
        self.capacity_kwh = capacity_kwh
        self.nominal_charge_kw = nominal_charge_kw
        self.nominal_discharge_kw = nominal_discharge_kw
        self.soc_pct = initial_soc_pct
        self.cell_temp_c = 19.5
        self.heater_mode = "AUTO"
        self.heater_active = True
        self.heater_power_kw = 4.2
        self.cycles = 412.5

    def step(self, net_power_kw: float, ambient_temp_c: float, dt_hours: float) -> Dict[str, Any]:
        """
        Updates battery state:
        net_power_kw > 0 -> surplus generation, charges battery
        net_power_kw < 0 -> deficit, discharges battery to load
        """
        cap_factor = get_capacity_factor(self.cell_temp_c)
        rate_factor = get_rate_factor(self.cell_temp_c)
        effective_capacity = self.capacity_kwh * cap_factor
        max_chg = self.nominal_charge_kw * rate_factor
        max_dis = self.nominal_discharge_kw * rate_factor

        current_kwh = effective_capacity * (self.soc_pct / 100.0)

        actual_flow_kw = 0.0
        if net_power_kw > 0:
            # Charging with 95% roundtrip efficiency
            charge_power = min(net_power_kw, max_chg)
            headroom = (effective_capacity * 0.98) - current_kwh
            actual_flow_kw = min(charge_power, max(0.0, headroom / max(0.001, dt_hours)))
            current_kwh += actual_flow_kw * dt_hours * 0.95
        elif net_power_kw < 0:
            # Discharging with 95% efficiency
            demand_kw = min(abs(net_power_kw), max_dis)
            available = current_kwh - (effective_capacity * 0.15)  # 15% critical reserve
            actual_flow_kw = -min(demand_kw, max(0.0, available / max(0.001, dt_hours)))
            current_kwh += actual_flow_kw * dt_hours / 0.95

        self.soc_pct = round(max(5.0, min(100.0, (current_kwh / effective_capacity) * 100.0)), 1)
        self.cycles += abs(actual_flow_kw * dt_hours) / (2.0 * self.capacity_kwh)

        # Thermal dynamics: ambient cooling vs heating jacket
        heat_loss = (self.cell_temp_c - ambient_temp_c) * 0.015 * dt_hours
        internal_i2r_heating = (abs(actual_flow_kw) / 100.0) * 0.3 * dt_hours
        heater_gain = (self.heater_power_kw * 0.15 * dt_hours) if self.heater_active else 0.0

        self.cell_temp_c = round(self.cell_temp_c - heat_loss + internal_i2r_heating + heater_gain, 1)

        # Auto-maintain cell temp between 16°C and 22°C
        if self.heater_mode == "AUTO":
            self.heater_active = self.cell_temp_c < 18.0

        return {
            "bess_soc_pct": self.soc_pct,
            "bess_flow_kw": round(actual_flow_kw, 1),
            "bess_stored_kwh": round(current_kwh, 1),
            "effective_capacity_kwh": round(effective_capacity, 1),
            "cell_temp_c": self.cell_temp_c,
            "heater_active": self.heater_active,
            "heater_draw_kw": self.heater_power_kw if self.heater_active else 0.0,
            "cycles_completed": round(self.cycles, 1),
        }
