"""
PolarEMS Multi-Objective Cost & Penalty Functions
Balances fuel conservation, emission reductions, and battery lifecycle preservation.
"""

from typing import Dict, Any


class DispatchObjectives:
    """Multi-objective cost evaluator for 24h dispatch schedules."""

    def __init__(
        self,
        diesel_fuel_price_usd_per_liter: float = 2.40,  # High logistical cost to ship fuel to Antarctica
        co2_carbon_penalty_usd_per_kg: float = 0.08,
        battery_degradation_cost_usd_per_cycle: float = 4.50,
    ):
        self.fuel_price = diesel_fuel_price_usd_per_liter
        self.carbon_penalty = co2_carbon_penalty_usd_per_kg
        self.batt_degradation_cost = battery_degradation_cost_usd_per_cycle

    def evaluate_cost(
        self,
        diesel_liters: float,
        co2_kg: float,
        battery_throughput_kwh: float,
        bess_capacity_kwh: float = 500.0,
    ) -> Dict[str, float]:
        fuel_cost = diesel_liters * self.fuel_price
        emission_cost = co2_kg * self.carbon_penalty
        cycles = battery_throughput_kwh / (2.0 * bess_capacity_kwh)
        degradation_cost = cycles * self.batt_degradation_cost

        total_cost = fuel_cost + emission_cost + degradation_cost

        return {
            "total_dispatch_cost_usd": round(total_cost, 2),
            "fuel_cost_usd": round(fuel_cost, 2),
            "emission_penalty_usd": round(emission_cost, 2),
            "battery_wear_cost_usd": round(degradation_cost, 2),
        }
