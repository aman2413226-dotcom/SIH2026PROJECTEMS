"""
PolarEMS Physical Constants & Lookup Tables
"""

import numpy as np

# Battery Cold-Weather Temperature Derating Curves (LFP / NMC Polar Storage)
TEMP_POINTS = [-40.0, -30.0, -20.0, -10.0, 0.0, 10.0, 25.0]
CAPACITY_DERATE_FACTORS = [0.15, 0.30, 0.50, 0.70, 0.85, 0.95, 1.00]
RATE_DERATE_FACTORS = [0.20, 0.35, 0.55, 0.75, 0.90, 1.00, 1.00]


def get_capacity_factor(temp_c: float) -> float:
    """Returns effective capacity factor (0.15 to 1.0) based on cell/battery temperature."""
    return float(np.interp(temp_c, TEMP_POINTS, CAPACITY_DERATE_FACTORS))


def get_rate_factor(temp_c: float) -> float:
    """Returns charge/discharge rate factor (0.20 to 1.0) based on cell/battery temperature."""
    return float(np.interp(temp_c, TEMP_POINTS, RATE_DERATE_FACTORS))


def calculate_wind_chill(ambient_temp_c: float, wind_speed_ms: float) -> float:
    """
    Standard Jag/TI Polar Wind Chill Index Formula:
    T_wc = 13.12 + 0.6215*T - 11.37*(V*3.6)^0.16 + 0.3965*T*(V*3.6)^0.16
    """
    v_kmh = max(0.1, wind_speed_ms * 3.6)
    wind_chill = (
        13.12
        + (0.6215 * ambient_temp_c)
        - (11.37 * (v_kmh ** 0.16))
        + (0.3965 * ambient_temp_c * (v_kmh ** 0.16))
    )
    return round(float(wind_chill), 1)


# Emission Factors
DIESEL_CO2_KG_PER_LITER = 2.68  # EPA standard for polar marine/industrial gasoil
DIESEL_SOX_G_PER_LITER = 1.2
DIESEL_NOX_G_PER_LITER = 8.5
DIESEL_PM_G_PER_LITER = 0.45

# Grid Constants
GRID_FREQUENCY_NOMINAL_HZ = 50.0
GRID_VOLTAGE_NOMINAL_V = 400.0
