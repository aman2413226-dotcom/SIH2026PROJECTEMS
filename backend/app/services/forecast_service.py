import math
from typing import Dict, Any, List
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import json

from backend.app.services.dataset_service import dataset_service

try:
    from lightgbm import LGBMRegressor
    HAS_LIGHTGBM = True
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor
    HAS_LIGHTGBM = False


class PolarForecastService:
    """
    Service for predictive 24-hour forecasting of station electrical/thermal loads
    and solar/wind renewable output in extreme polar environments.
    """

    MODEL_DIR = Path(__file__).resolve().parent.parent.parent.parent / "ai" / "saved_models"
    METADATA_PATH = MODEL_DIR / "model_metadata.json"

    FEATURE_COLS = [
        "ambient_temp_c",
        "wind_speed_ms",
        "hour_sin",
        "hour_cos",
        "day_of_year",
        "is_polar_day",
        "wind_chill_c",
    ]
    
    TARGETS = ["load_demand_kw", "solar_output_kw", "wind_output_kw"]

    def __init__(self):
        self.models = {
            "load_demand_kw": None,
            "solar_output_kw": None,
            "wind_output_kw": None
        }
        self.metadata: Dict[str, Any] = {}
        self._ensure_model_ready()

    def _ensure_model_ready(self):
        """Loads serialized models or trains fresh on Antarctic data."""
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        
        all_models_exist = all((self.MODEL_DIR / f"{target}_model.pkl").exists() for target in self.TARGETS)
        
        if all_models_exist and self.METADATA_PATH.exists():
            try:
                for target in self.TARGETS:
                    self.models[target] = joblib.load(self.MODEL_DIR / f"{target}_model.pkl")
                with open(self.METADATA_PATH, "r") as f:
                    self.metadata = json.load(f)
                self.metadata["status"] = "LOADED_FROM_DISK"
                return
            except Exception:
                pass

        # Train models
        self._train_and_save_model()

    def _train_and_save_model(self):
        """Trains LightGBM models for all targets and saves to disk."""
        df = dataset_service.get_real_dataset()
        X = df[self.FEATURE_COLS]
        
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        
        self.metadata = {
            "model_type": "LightGBM Regressor" if HAS_LIGHTGBM else "GradientBoostingRegressor",
            "status": "TRAINED_AND_SAVED",
            "training_days": len(df) // 24,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "calibration_source": "Bharati Research Station Dataset (NCPOR/Kaggle)",
            "models": {}
        }

        for target in self.TARGETS:
            y = df[target]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

            if HAS_LIGHTGBM:
                model = LGBMRegressor(
                    n_estimators=250,
                    learning_rate=0.04,
                    max_depth=6,
                    num_leaves=31,
                    random_state=42,
                    verbose=-1,
                )
            else:
                model = GradientBoostingRegressor(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=5,
                    random_state=42,
                )

            model.fit(X_train, y_train)
            self.models[target] = model

            # Evaluate
            preds = model.predict(X_test)
            mae = float(np.mean(np.abs(preds - y_test)))
            r2 = float(1.0 - (np.sum((y_test - preds) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2)))

            self.metadata["models"][target] = {
                "r2_score": round(r2, 3),
                "mae_kw": round(mae, 2),
                "feature_importances": dict(zip(self.FEATURE_COLS, [round(float(v), 4) for v in model.feature_importances_])),
            }
            
            # Save to disk
            try:
                joblib.dump(model, self.MODEL_DIR / f"{target}_model.pkl")
            except Exception:
                pass
                
        try:
            with open(self.METADATA_PATH, "w") as f:
                json.dump(self.metadata, f, indent=4)
        except Exception:
            pass

    def predict_24h_load(
        self,
        current_temp_c: float = -52.0,
        current_wind_speed_ms: float = 14.5,
        day_of_year: int = 240,
        start_hour: int = 0,
    ) -> List[Dict[str, Any]]:
        """Generates 24-hour ahead station demand forecast using the trained ML model."""
        forecast = []
        is_polar_day = 1 if (day_of_year <= 45 or day_of_year >= 315) else (0 if (125 <= day_of_year <= 225) else 0.5)

        for step in range(24):
            hour = (start_hour + step) % 24
            # Model temperature and wind progression over the day
            temp_step = current_temp_c + (math.sin(hour * 0.26) * 1.5)
            wind_step = max(2.0, current_wind_speed_ms + (math.cos(hour * 0.26) * 2.0))

            v_kmh = max(0.1, wind_step * 3.6)
            wind_chill = round(13.12 + (0.6215 * temp_step) - (11.37 * (v_kmh ** 0.16)) + (0.3965 * temp_step * (v_kmh ** 0.16)), 1)

            feature_vec = pd.DataFrame([{
                "ambient_temp_c": temp_step,
                "wind_speed_ms": wind_step,
                "hour_sin": math.sin(2 * math.pi * hour / 24.0),
                "hour_cos": math.cos(2 * math.pi * hour / 24.0),
                "day_of_year": day_of_year,
                "is_polar_day": is_polar_day,
                "wind_chill_c": wind_chill,
            }])

            predicted_total = float(self.models["load_demand_kw"].predict(feature_vec)[0])
            electrical_base = round(76.0 + (math.sin(hour * 0.26) * 5.0), 1)
            thermal_heating = round(max(0.0, predicted_total - electrical_base), 1)

            forecast.append({
                "hour_ahead": step + 1,
                "clock_hour": f"{hour:02d}:00 UTC",
                "ambient_temp_c": round(temp_step, 1),
                "wind_speed_ms": round(wind_step, 1),
                "wind_chill_c": wind_chill,
                "electrical_load_kw": electrical_base,
                "thermal_heating_load_kw": thermal_heating,
                "total_station_demand_kw": round(predicted_total, 1),
            })

        return forecast

    def predict_24h_renewables(
        self,
        station_latitude: float = -70.7667,
        day_of_year: int = 240,
        start_hour: int = 0,
        base_wind_speed_ms: float = 14.5,
    ) -> List[Dict[str, Any]]:
        """Predicts solar and wind generation for the upcoming 24 hours using trained ML models."""
        forecast = []
        is_polar_day = 1 if (day_of_year <= 45 or day_of_year >= 315) else (0 if (125 <= day_of_year <= 225) else 0.5)
        
        for step in range(24):
            hour = (start_hour + step) % 24
            
            # Baseline weather (should match load forecast assumption)
            wind_speed = round(max(2.0, base_wind_speed_ms + (math.sin(hour * 0.26) * 3.5) + (step % 3 * 0.5)), 1)
            temp = -15.0 # baseline temp assumption for renewables if not provided
            
            v_kmh = max(0.1, wind_speed * 3.6)
            wind_chill = round(13.12 + (0.6215 * temp) - (11.37 * (v_kmh ** 0.16)) + (0.3965 * temp * (v_kmh ** 0.16)), 1)

            feature_vec = pd.DataFrame([{
                "ambient_temp_c": temp,
                "wind_speed_ms": wind_speed,
                "hour_sin": math.sin(2 * math.pi * hour / 24.0),
                "hour_cos": math.cos(2 * math.pi * hour / 24.0),
                "day_of_year": day_of_year,
                "is_polar_day": is_polar_day,
                "wind_chill_c": wind_chill,
            }])

            # Predict using models
            predicted_solar = max(0.0, float(self.models["solar_output_kw"].predict(feature_vec)[0]))
            predicted_wind = max(0.0, float(self.models["wind_output_kw"].predict(feature_vec)[0]))
            
            # Additional logic for physics context (display only)
            declination = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
            lat_rad = math.radians(station_latitude)
            dec_rad = math.radians(declination)
            ha_rad = math.radians((hour - 12.0) * 15.0)

            sin_elev = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad)
            elevation_deg = math.degrees(math.asin(max(-1.0, min(1.0, sin_elev))))
            
            if elevation_deg > 0.0:
                ghi = round(1050.0 * (elevation_deg / 45.0) ** 0.85 * 0.9, 1)
            else:
                ghi = 0.0
                predicted_solar = 0.0 # Force night to 0
                
            wind_status = "NORMAL_GENERATION"
            if wind_speed < 3.0:
                wind_status = "BELOW_CUTIN"
                predicted_wind = 0.0
            elif wind_speed >= 25.0:
                wind_status = "STORM_CUTOUT"
                predicted_wind = 0.0

            forecast.append({
                "hour_ahead": step + 1,
                "clock_hour": f"{hour:02d}:00 UTC",
                "solar_elevation_deg": round(max(0.0, elevation_deg), 1),
                "ghi_wm2": ghi,
                "forecast_solar_kw": round(predicted_solar, 1),
                "forecast_wind_speed_ms": wind_speed,
                "wind_status": wind_status,
                "forecast_wind_kw": round(predicted_wind, 1),
                "total_renewable_kw": round(predicted_solar + predicted_wind, 1),
            })

        return forecast

forecast_service = PolarForecastService()
