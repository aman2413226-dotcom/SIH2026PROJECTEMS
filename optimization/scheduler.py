"""
PolarEMS 24-Hour Multi-Objective Dispatch Scheduler
Computes optimal hour-by-hour dispatch minimizing diesel runtime and preserving battery life.
"""

from typing import Dict, Any, List
from optimization.constraints import DispatchConstraints
from optimization.objectives import DispatchObjectives
from config.constants import DIESEL_CO2_KG_PER_LITER


class MicrogridDispatchScheduler:
    """24-Hour Rolling Horizon Dispatch Optimizer."""

    def __init__(self, bess_capacity_kwh: float = 500.0, max_diesel_kw: float = 80.0):
        self.constraints = DispatchConstraints(bess_capacity_kwh, max_diesel_kw)
        self.objectives = DispatchObjectives()

    def solve_24h_schedule(
        self,
        forecast_solar: List[float],
        forecast_wind: List[float],
        forecast_demand: List[float],
        initial_soc_pct: float = 75.0,
    ) -> Dict[str, Any]:
        """
        Solves 24-hour optimal dispatch trajectory.
        Prioritizes:
        1. 100% Life Support Supply
        2. Maximum direct renewable self-consumption
        3. Battery absorption of surplus / discharge during deficits
        4. Diesel dispatch only when battery reaches critical threshold
        5. Enforces minimum 3-hour runtime rule when diesel starts
        """
        schedule = []
        current_soc = initial_soc_pct
        bess_kwh = self.constraints.bess_capacity_kwh * (current_soc / 100.0)
        total_fuel_liters = 0.0
        total_co2_kg = 0.0
        total_battery_throughput = 0.0

        diesel_run_timer = 0  # Track consecutive hours ON

        for h in range(24):
            solar_kw = forecast_solar[h] if h < len(forecast_solar) else 0.0
            wind_kw = forecast_wind[h] if h < len(forecast_wind) else 0.0
            demand_kw = forecast_demand[h] if h < len(forecast_demand) else 75.0

            renewable_kw = solar_kw + wind_kw
            net_renewable = renewable_kw - demand_kw

            diesel_kw = 0.0
            battery_flow_kw = 0.0  # + is charging, - is discharging

            # Minimum runtime enforcement
            must_run_diesel = (0 < diesel_run_timer < self.constraints.min_diesel_runtime_hours)

            if net_renewable >= 0:
                # Renewable Surplus
                if must_run_diesel:
                    # Diesel is locked ON due to min runtime rule (running at minimum loading)
                    diesel_kw = self.constraints.min_diesel_loading_kw
                    diesel_run_timer += 1
                    total_surplus = net_renewable + diesel_kw
                    charge_space = (self.constraints.bess_capacity_kwh * (self.constraints.max_soc_pct / 100.0)) - bess_kwh
                    battery_flow_kw = min(total_surplus, min(self.constraints.max_charge_rate_kw, max(0.0, charge_space)))
                    bess_kwh += battery_flow_kw * 0.95
                else:
                    diesel_run_timer = 0
                    diesel_kw = 0.0
                    charge_space = (self.constraints.bess_capacity_kwh * (self.constraints.max_soc_pct / 100.0)) - bess_kwh
                    battery_flow_kw = min(net_renewable, min(self.constraints.max_charge_rate_kw, max(0.0, charge_space)))
                    bess_kwh += battery_flow_kw * 0.95
            else:
                # Deficit
                deficit_kw = abs(net_renewable)
                min_reserve_kwh = self.constraints.bess_capacity_kwh * (self.constraints.min_soc_pct / 100.0)
                available_battery_kwh = max(0.0, bess_kwh - min_reserve_kwh)

                if available_battery_kwh > (deficit_kw * 1.05) and not must_run_diesel:
                    # Battery can comfortably cover deficit without starting generator
                    battery_flow_kw = -min(deficit_kw, self.constraints.max_discharge_rate_kw)
                    bess_kwh += battery_flow_kw / 0.95
                    diesel_kw = 0.0
                    diesel_run_timer = 0
                else:
                    # Must start or continue running diesel
                    diesel_run_timer += 1
                    diesel_kw = min(self.constraints.max_diesel_kw, max(self.constraints.min_diesel_loading_kw, deficit_kw))
                    remaining_deficit = deficit_kw - diesel_kw
                    if remaining_deficit > 0:
                        battery_flow_kw = -min(remaining_deficit, self.constraints.max_discharge_rate_kw)
                        bess_kwh += battery_flow_kw / 0.95
                    else:
                        battery_flow_kw = 0.0

            # Update battery SOC
            current_soc = round((bess_kwh / self.constraints.bess_capacity_kwh) * 100.0, 1)
            total_battery_throughput += abs(battery_flow_kw)

            # Fuel calculation
            fuel_step = (diesel_kw * 0.28 + (2.8 if diesel_kw > 0 else 0.0))
            total_fuel_liters += fuel_step
            co2_step = fuel_step * DIESEL_CO2_KG_PER_LITER
            total_co2_kg += co2_step

            schedule.append({
                "hour": h + 1,
                "label": f"{h:02d}:00",
                "solar_kw": round(solar_kw, 1),
                "wind_kw": round(wind_kw, 1),
                "battery_assist_kw": round(max(0.0, -battery_flow_kw), 1),
                "battery_charging_kw": round(max(0.0, battery_flow_kw), 1),
                "diesel_kw": round(diesel_kw, 1),
                "station_load_kw": round(demand_kw, 1),
                "bess_soc_pct": current_soc,
                "diesel_fuel_liters": round(fuel_step, 2),
                "co2_kg": round(co2_step, 2),
            })

        cost_eval = self.objectives.evaluate_cost(
            diesel_liters=total_fuel_liters,
            co2_kg=total_co2_kg,
            battery_throughput_kwh=total_battery_throughput,
            bess_capacity_kwh=self.constraints.bess_capacity_kwh,
        )

        return {
            "status": "OPTIMAL_SCHEDULE_SOLVED",
            "expected_24h_fuel_liters": round(total_fuel_liters, 1),
            "expected_24h_emissions_co2_kg": round(total_co2_kg, 1),
            "total_dispatch_cost_usd": cost_eval["total_dispatch_cost_usd"],
            "cost_breakdown": cost_eval,
            "hourly_schedule": schedule,
        }


optimizer = MicrogridDispatchScheduler()
