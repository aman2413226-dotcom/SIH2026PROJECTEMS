"""
PolarEMS Dispatch Constraints
Defines operational physical constraints for microgrid generation, storage, and life support.
"""

from typing import Dict, Any


class DispatchConstraints:
    """Microgrid physical operational limits."""

    def __init__(self, bess_capacity_kwh: float = 500.0, max_diesel_kw: float = 80.0):
        self.bess_capacity_kwh = bess_capacity_kwh
        self.min_soc_pct = 20.0  # Life support emergency reserve
        self.max_soc_pct = 95.0
        self.max_charge_rate_kw = 100.0
        self.max_discharge_rate_kw = 100.0
        self.max_diesel_kw = max_diesel_kw
        self.min_diesel_loading_kw = 25.0  # Avoid wet-stacking in cold weather
        self.min_diesel_runtime_hours = 3  # Anti-short-cycling constraint
        self.spinning_reserve_margin_kw = 15.0

    def check_power_balance(self, generation_kw: float, demand_kw: float, tolerance_kw: float = 0.5) -> bool:
        return abs(generation_kw - demand_kw) <= tolerance_kw

    def is_soc_valid(self, soc_pct: float) -> bool:
        return self.min_soc_pct <= soc_pct <= self.max_soc_pct
