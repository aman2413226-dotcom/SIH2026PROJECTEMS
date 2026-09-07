"use client";

import React, { useState, useEffect } from "react";
import { ThemeToggle } from "./components/theme-toggle";
import {
  Zap,
  Sun,
  Wind,
  Battery,
  Fuel,
  CloudRain,
  Shield,
  AlertTriangle,
  Play,
  Pause,
  RotateCcw,
  FastForward,
  CheckCircle2,
  Terminal,
  Activity,
  Flame,
  Radio,
  Sliders,
  Thermometer,
  Compass,
} from "lucide-react";

export default function PolarEMSDashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [apiOnline, setApiOnline] = useState(true);
  const [activeStation, setActiveStation] = useState("MAITRI");

  // Telemetry States
  const [telemetry, setTelemetry] = useState<any>(null);
  const [powerFlow, setPowerFlow] = useState<any>(null);
  const [securityStatus, setSecurityStatus] = useState<any>(null);
  const [dispatchData, setDispatchData] = useState<any>(null);
  const [faults, setFaults] = useState<any[]>([]);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const API_BASE = "http://localhost:8000/api/v1";

  // Fetch telemetry every 1.5 seconds
  useEffect(() => {
    let isMounted = true;

    async function pollTelemetry() {
      try {
        const [dashRes, flowRes, secRes, fltRes] = await Promise.all([
          fetch(`${API_BASE}/dashboard/overview`).catch(() => null),
          fetch(`${API_BASE}/dashboard/power-flow`).catch(() => null),
          fetch(`${API_BASE}/security/status`).catch(() => null),
          fetch(`${API_BASE}/faults/active`).catch(() => null),
        ]);

        if (dashRes && dashRes.ok) {
          const dash = await dashRes.json();
          if (isMounted) setTelemetry(dash);
          setApiOnline(true);
        } else {
          setApiOnline(false);
        }

        if (flowRes && flowRes.ok) {
          const flow = await flowRes.json();
          if (isMounted) setPowerFlow(flow);
        }

        if (secRes && secRes.ok) {
          const sec = await secRes.json();
          if (isMounted) setSecurityStatus(sec);
        }

        if (fltRes && fltRes.ok) {
          const flt = await fltRes.json();
          if (isMounted) setFaults(flt);
        }
      } catch (err) {
        setApiOnline(false);
      }
    }

    pollTelemetry();
    const interval = setInterval(pollTelemetry, 1500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [activeStation]);

  // Fetch 24h dispatch when entering dispatch tab
  useEffect(() => {
    if (activeTab === "dispatch") {
      fetch(`${API_BASE}/forecast/optimal-dispatch-schedule`)
        .then((res) => res.json())
        .then((data) => setDispatchData(data))
        .catch(() => { });
    }
  }, [activeTab]);



  const handleStationSwitch = async (station: string) => {
    setLoadingAction("station");
    try {
      await fetch(`${API_BASE}/weather/switch-station`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ station }),
      });
      setActiveStation(station);
    } catch (e) { }
    setLoadingAction(null);
  };



  // Red Team Cyber-Attack Actions
  const handleRedTeamAttack = async (attackType: string) => {
    setLoadingAction(attackType);
    try {
      await fetch(`${API_BASE}/security/attack/${attackType}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ surge_kw: 95.0 }),
      });
      const secRes = await fetch(`${API_BASE}/security/status`);
      if (secRes.ok) setSecurityStatus(await secRes.json());
    } catch (e) { }
    setLoadingAction(null);
  };

  const handleResetPosture = async () => {
    setLoadingAction("reset-posture");
    try {
      await fetch(`${API_BASE}/security/reset`, { method: "POST" });
      const secRes = await fetch(`${API_BASE}/security/status`);
      if (secRes.ok) setSecurityStatus(await secRes.json());
    } catch (e) { }
    setLoadingAction(null);
  };

  // Safe fallback values
  const pb = telemetry?.power_balance || { total_load_kw: 112.5, total_generation_kw: 112.5, renewable_fraction_pct: 78.4 };
  const gen = telemetry?.generation_sources || { solar_pv_kw: 28.5, wind_turbines_kw: 54.0, diesel_generators_kw: 30.0 };
  const auto = telemetry?.autonomy || { battery_soc_pct: 78.5, battery_cell_temp_c: 19.5, fuel_reserve_liters: 45200, projected_fuel_days: 72.0 };
  const isCompromised = securityStatus?.posture === "COMPROMISED";

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#070b13] text-slate-900 dark:text-slate-100 flex flex-col font-sans">
      {/* Top Header Bar */}
      <header className="border-b border-slate-200/80 dark:border-slate-800/80 bg-white/90 dark:bg-[#0c1322]/90 backdrop-blur sticky top-0 z-50 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-tr from-cyan-500 to-teal-400 p-0.5 shadow-lg shadow-cyan-500/20">
            <div className="h-full w-full bg-slate-200 dark:bg-slate-950 rounded-[7px] flex items-center justify-center">
              <Zap className="h-5 w-5 text-cyan-400 fill-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-black tracking-wider text-xl bg-gradient-to-r from-white via-slate-100 to-cyan-300 bg-clip-text text-transparent">
                PolarEMS
              </span>
              <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                INDUSTRIAL V1.0
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Antarctic Microgrid Energy Management &amp; Digital Twin</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-100 dark:bg-slate-100/90 dark:bg-slate-900/90 p-1 rounded-xl border border-slate-200 dark:border-slate-800">
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${activeTab === "dashboard"
              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
              : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:text-slate-200"
              }`}
          >
            <Activity className="h-3.5 w-3.5" /> Mission Control
          </button>
          <button
            onClick={() => setActiveTab("dispatch")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${activeTab === "dispatch"
              ? "bg-teal-500/20 text-teal-300 border border-teal-500/40 shadow-sm"
              : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:text-slate-200"
              }`}
          >
            <Zap className="h-3.5 w-3.5" /> 24h AI Dispatch
          </button>
          <button
            onClick={() => setActiveTab("diagnostics")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${activeTab === "diagnostics"
              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm"
              : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:text-slate-200"
              }`}
          >
            <AlertTriangle className="h-3.5 w-3.5" /> Diagnostics &amp; Alarms
            {faults.length > 0 && (
              <span className="h-4 w-4 rounded-full bg-amber-500 text-black font-bold text-[10px] flex items-center justify-center">
                {faults.length}
              </span>
            )}
          </button>
        </nav>

        {/* Live Weather Cluster & Controls */}
        <div className="flex items-center gap-4 text-xs">
          {/* Station Switcher */}
          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-1">
            <Compass className="h-3.5 w-3.5 text-cyan-400 ml-1" />
            <select
              value={activeStation}
              onChange={(e) => handleStationSwitch(e.target.value)}
              className="bg-transparent text-slate-700 dark:text-slate-200 font-semibold focus:outline-none cursor-pointer pr-2"
            >

              <option value="BHARATI" className="bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100">
                Bharati Station (Larsemann)
              </option>
            </select>
          </div>

          {/* Meteorological Badges */}
          <div className="hidden lg:flex items-center gap-2">
            <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-cyan-300 flex items-center gap-1.5">
              <Thermometer className="h-3.5 w-3.5 text-cyan-400" />
              <b>{telemetry?.ambient_temperature_c?.toFixed(1) || "-52.4"}°C</b>
              <span className="text-[10px] text-slate-500 dark:text-slate-400">(Chill: {telemetry?.wind_chill_c?.toFixed(1) || "-65.2"}°C)</span>
            </span>
            <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-teal-300 flex items-center gap-1.5">
              <Wind className="h-3.5 w-3.5 text-teal-400" />
              <b>14.8 m/s</b>
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Katabatic</span>
            </span>
            <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-amber-300 flex items-center gap-1.5">
              <Sun className="h-3.5 w-3.5 text-amber-400" />
              <b>320 W/m²</b>
            </span>
          </div>

          {/* Online Indicator */}
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-100/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
            <span
              className={`h-2 w-2 rounded-full ${apiOnline ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
                }`}
            />
            <span className="text-[11px] font-semibold tracking-wide text-slate-600 dark:text-slate-300">
              {apiOnline ? "NCPOR LIVE" : "OFFLINE"}
            </span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 p-6 space-y-6 max-w-[1700px] w-full mx-auto">
        {/* KPI Telemetry Stat Cards */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* 1. Station Demand */}
          <div className="bg-white dark:bg-[#0e1626] border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Station Demand</span>
              <Zap className="h-4 w-4 text-cyan-400" />
            </div>
            <div className="flex items-baseline gap-1.5 mb-1">
              <span className="text-2xl font-black text-slate-900 dark:text-white">{pb.total_load_kw?.toFixed(1) || "112.5"}</span>
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">kW</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between">
              <span>Thermal Heating:</span>
              <b className="text-cyan-300">{telemetry?.consumption_breakdown?.life_support_heating_kw?.toFixed(1) || "42.0"} kW</b>
            </div>
            <div className="mt-3 h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-teal-400 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (pb.total_load_kw / 160) * 100)}%` }}
              />
            </div>
          </div>

          {/* 2. Renewable Output */}
          <div className="bg-white dark:bg-[#0e1626] border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Renewable Output</span>
              <Sun className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="flex items-baseline gap-1.5 mb-1">
              <span className="text-2xl font-black text-emerald-300">
                {((gen.solar_pv_kw || 0) + (gen.wind_turbines_kw || 0)).toFixed(1)}
              </span>
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">kW</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between">
              <span>Penetration:</span>
              <b className="text-emerald-400">{pb.renewable_fraction_pct?.toFixed(1) || "78.4"}%</b>
            </div>
            <div className="mt-3 h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-400 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, pb.renewable_fraction_pct || 75)}%` }}
              />
            </div>
          </div>

          {/* 3. BESS Battery SOC */}
          <div className="bg-white dark:bg-[#0e1626] border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">BESS Battery SOC</span>
              <Battery className="h-4 w-4 text-blue-400" />
            </div>
            <div className="flex items-baseline gap-1.5 mb-1">
              <span className="text-2xl font-black text-blue-300">{auto.battery_soc_pct?.toFixed(1) || "78.5"}</span>
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">%</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between">
              <span>Core Pack Temp:</span>
              <b className="text-blue-300">{auto.battery_cell_temp_c?.toFixed(1) || "19.5"}°C</b>
            </div>
            <div className="mt-3 h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, auto.battery_soc_pct || 78)}%` }}
              />
            </div>
          </div>

          {/* 4. Diesel Powerplant Reserve */}
          <div className="bg-white dark:bg-[#0e1626] border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Diesel Reserve</span>
              <Fuel className="h-4 w-4 text-amber-400" />
            </div>
            <div className="flex items-baseline gap-1.5 mb-1">
              <span className="text-2xl font-black text-amber-300">
                {Math.round(auto.fuel_reserve_liters || 45200).toLocaleString()}
              </span>
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">L</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between">
              <span>Endurance:</span>
              <b className="text-amber-400">{auto.projected_fuel_days?.toFixed(1) || "72.0"} Days</b>
            </div>
            <div className="mt-3 h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-400 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (auto.fuel_reserve_liters / 50000) * 100)}%` }}
              />
            </div>
          </div>

          {/* 5. Carbon Emissions */}
          <div className="bg-white dark:bg-[#0e1626] border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Carbon Tracking</span>
              <CloudRain className="h-4 w-4 text-rose-400" />
            </div>
            <div className="flex items-baseline gap-1.5 mb-1">
              <span className="text-2xl font-black text-rose-300">
                {((gen.diesel_generators_kw || 0) * 0.28 * 2.68).toFixed(1)}
              </span>
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">kg/h</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between">
              <span>Cumulative CO2:</span>
              <b className="text-slate-600 dark:text-slate-300">11.04 t</b>
            </div>
            <div className="mt-3 h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-rose-500 rounded-full" style={{ width: "35%" }} />
            </div>
          </div>
        </section>

        {/* Tab 1: Dashboard & Power Flow */}
        {activeTab === "dashboard" && (
          <div className="grid grid-cols-1 gap-6">
            {/* Interactive Animated Power Flow Diagram */}
            <div className="bg-white dark:bg-[#0d1525] border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-xl relative flex flex-col">
              <div className="flex items-center justify-between mb-4 border-b border-slate-200/80 dark:border-slate-800/80 pb-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Zap className="h-5 w-5 text-cyan-400" />
                    Microgrid Central Bus &amp; Power Flow Map
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Real-time bidirectional power transfer between Generation, Storage, and Habitat Life Support
                  </p>
                </div>
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  400V 50Hz SYNCHRONIZED
                </span>
              </div>

              {/* Power Flow SVG Visualization */}
              <div className="flex-1 min-h-[380px] relative bg-slate-100/60 dark:bg-slate-950/60 rounded-xl border border-slate-200/60 dark:border-slate-800/60 p-6 flex items-center justify-center">
                <svg className="w-full h-full max-h-[350px]" viewBox="0 0 800 320" fill="none">
                  {/* Flow Paths */}
                  {/* Solar to Central Bus */}
                  <path d="M 160 60 L 400 160" stroke="#f59e0b" strokeWidth="3" className="flow-anim opacity-80" />
                  {/* Wind to Central Bus */}
                  <path d="M 160 160 L 400 160" stroke="#10b981" strokeWidth="3" className="flow-anim opacity-80" />
                  {/* Diesel to Central Bus */}
                  <path d="M 160 260 L 400 160" stroke="#f43f5e" strokeWidth="3" className="flow-anim opacity-80" />

                  {/* Central Bus to BESS (bidirectional) */}
                  <path d="M 400 160 L 640 80" stroke="#38bdf8" strokeWidth="3.5" className="flow-anim opacity-90" />
                  {/* Central Bus to Station Loads */}
                  <path d="M 400 160 L 640 240" stroke="#a855f7" strokeWidth="4" className="flow-anim opacity-90" />

                  {/* Generation Nodes */}
                  {/* Solar Node */}
                  <g transform="translate(40, 30)">
                    <rect width="120" height="60" rx="8" fill="currentColor" className="text-slate-100 dark:text-slate-800" stroke="#f59e0b" strokeWidth="1.5" />
                    <text x="60" y="24" fill="currentColor" className="text-slate-600 dark:text-slate-300" fontSize="11" fontWeight="bold" textAnchor="middle">
                      SOLAR PV
                    </text>
                    <text x="60" y="44" fill="#fbbf24" fontSize="14" fontWeight="black" textAnchor="middle">
                      {gen.solar_pv_kw?.toFixed(1) || "28.5"} kW
                    </text>
                  </g>

                  {/* Wind Node */}
                  <g transform="translate(40, 130)">
                    <rect width="120" height="60" rx="8" fill="currentColor" className="text-slate-100 dark:text-slate-800" stroke="#10b981" strokeWidth="1.5" />
                    <text x="60" y="24" fill="currentColor" className="text-slate-600 dark:text-slate-300" fontSize="11" fontWeight="bold" textAnchor="middle">
                      WIND TURBINES
                    </text>
                    <text x="60" y="44" fill="#34d399" fontSize="14" fontWeight="black" textAnchor="middle">
                      {gen.wind_turbines_kw?.toFixed(1) || "54.0"} kW
                    </text>
                  </g>

                  {/* Diesel Node */}
                  <g transform="translate(40, 230)">
                    <rect width="120" height="60" rx="8" fill="currentColor" className="text-slate-100 dark:text-slate-800" stroke="#f43f5e" strokeWidth="1.5" />
                    <text x="60" y="24" fill="currentColor" className="text-slate-600 dark:text-slate-300" fontSize="11" fontWeight="bold" textAnchor="middle">
                      DIESEL GENSETS
                    </text>
                    <text x="60" y="44" fill="#fb7185" fontSize="14" fontWeight="black" textAnchor="middle">
                      {gen.diesel_generators_kw?.toFixed(1) || "30.0"} kW
                    </text>
                  </g>

                  {/* Central Bus Node */}
                  <g transform="translate(340, 120)">
                    <rect width="120" height="80" rx="12" fill="currentColor" className="text-white dark:text-slate-900 glow-cyan" stroke="#38bdf8" strokeWidth="2.5" />
                    <text x="60" y="28" fill="currentColor" className="text-slate-500 dark:text-slate-400" fontSize="10" fontWeight="bold" textAnchor="middle">
                      AC CENTRAL BUS
                    </text>
                    <text x="60" y="48" fill="#38bdf8" fontSize="16" fontWeight="black" textAnchor="middle">
                      {pb.total_generation_kw?.toFixed(1) || "112.5"} kW
                    </text>
                    <text x="60" y="66" fill="currentColor" className="text-slate-400 dark:text-slate-500" fontSize="9" textAnchor="middle">
                      50.02 Hz | 400V
                    </text>
                  </g>

                  {/* BESS Node */}
                  <g transform="translate(640, 50)">
                    <rect width="130" height="65" rx="8" fill="currentColor" className="text-slate-100 dark:text-slate-800" stroke="#38bdf8" strokeWidth="1.5" />
                    <text x="65" y="22" fill="currentColor" className="text-slate-600 dark:text-slate-300" fontSize="11" fontWeight="bold" textAnchor="middle">
                      BESS STORAGE
                    </text>
                    <text x="65" y="42" fill="#38bdf8" fontSize="14" fontWeight="black" textAnchor="middle">
                      SOC {auto.battery_soc_pct?.toFixed(1) || "78.5"}%
                    </text>
                    <text x="65" y="56" fill="currentColor" className="text-slate-500 dark:text-slate-400" fontSize="10" textAnchor="middle">
                      {auto.battery_cell_temp_c?.toFixed(1) || "19.5"}°C Pack
                    </text>
                  </g>

                  {/* Station Loads Node */}
                  <g transform="translate(640, 205)">
                    <rect
                      width="130"
                      height="75"
                      rx="8"
                      fill="currentColor"
                      stroke={isCompromised ? "#f43f5e" : "#a855f7"}
                      strokeWidth={isCompromised ? "2.5" : "1.5"}
                      className={`text-slate-100 dark:text-slate-800 ${isCompromised ? "red-alert-glow" : ""}`}
                    />
                    <text x="65" y="22" fill="currentColor" className="text-slate-600 dark:text-slate-300" fontSize="11" fontWeight="bold" textAnchor="middle">
                      STATION LOADS
                    </text>
                    <text
                      x="65"
                      y="44"
                      fill={isCompromised ? "#f43f5e" : "#c084fc"}
                      fontSize="15"
                      fontWeight="black"
                      textAnchor="middle"
                    >
                      {pb.total_load_kw?.toFixed(1) || "112.5"} kW
                    </text>
                    <text x="65" y="62" fill="currentColor" className="text-slate-500 dark:text-slate-400" fontSize="9" textAnchor="middle">
                      Life Support Intact
                    </text>
                  </g>
                </svg>
              </div>
            </div>


          </div>
        )}

        {/* Tab 2: 24h AI Dispatch */}
        {activeTab === "dispatch" && (
          <div className="bg-white dark:bg-[#0d1525] border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Zap className="h-5 w-5 text-teal-400" />
                  24-Hour Multi-Objective Microgrid Dispatch Schedule
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  LightGBM seasonal load predictions optimized to minimize diesel runtime and protect BESS health
                </p>
              </div>
              <div className="flex gap-4 text-xs font-semibold">
                <span className="px-3 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300">
                  Expected 24h Fuel: <b>{dispatchData?.expected_24h_fuel_liters || 185} L</b>
                </span>
                <span className="px-3 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300">
                  Emissions: <b>{dispatchData?.expected_24h_emissions_co2_kg || 495} kg CO₂</b>
                </span>
              </div>
            </div>

            {/* Dispatch Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 bg-slate-100/50 dark:bg-slate-900/50">
                  <tr>
                    <th className="p-3">Hour UTC</th>
                    <th className="p-3">Station Load</th>
                    <th className="p-3">Solar PV</th>
                    <th className="p-3">Wind Power</th>
                    <th className="p-3">Battery Net</th>
                    <th className="p-3">Diesel Power</th>
                    <th className="p-3">Expected SOC</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {(dispatchData?.hourly_schedule || []).slice(0, 12).map((row: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-200/30 dark:bg-slate-800/30 transition-colors">
                      <td className="p-3 font-bold text-slate-600 dark:text-slate-300">{row.label}</td>
                      <td className="p-3 text-slate-900 dark:text-white font-semibold">{row.station_load_kw} kW</td>
                      <td className="p-3 text-amber-400">{row.solar_kw} kW</td>
                      <td className="p-3 text-emerald-400">{row.wind_kw} kW</td>
                      <td className="p-3 text-blue-400">
                        {row.battery_charging_kw > 0
                          ? `+${row.battery_charging_kw} kW (Charge)`
                          : `-${row.battery_assist_kw} kW (Assist)`}
                      </td>
                      <td className="p-3 text-rose-400">{row.diesel_kw > 0 ? `${row.diesel_kw} kW` : "OFF (0 kW)"}</td>
                      <td className="p-3 font-semibold text-slate-700 dark:text-slate-200">{row.bess_soc_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Diagnostics & Alarms */}
        {activeTab === "diagnostics" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white dark:bg-[#0d1525] border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-xl">
              <h2 className="text-base font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
                <AlertTriangle className="h-4 w-4 text-amber-400" />
                Active Microgrid Physical Diagnostics
              </h2>
              {faults.length === 0 ? (
                <div className="p-8 text-center text-slate-500 dark:text-slate-400 bg-slate-200 dark:bg-slate-100/40 dark:bg-slate-950/40 rounded-xl border border-slate-200 dark:border-slate-800">
                  <CheckCircle2 className="h-10 w-10 text-emerald-400 mx-auto mb-2 opacity-80" />
                  <p className="font-semibold text-slate-600 dark:text-slate-300">All Microgrid Telemetry Nominal</p>
                  <p className="text-xs">No active physical faults detected across wind, solar, or BESS.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {faults.map((f: any) => (
                    <div key={f.fault_id} className="p-4 rounded-xl bg-slate-100 dark:bg-slate-900 border border-amber-500/30 flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                            {f.fault_type}
                          </span>
                          <span className="text-xs font-bold text-slate-700 dark:text-slate-200">{f.system}</span>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-300 mb-1">{f.description}</p>
                        <p className="text-[11px] text-cyan-400">💡 AI Recommendation: {f.ai_recommendation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Winterization Status Card */}
            <div className="bg-white dark:bg-[#0d1525] border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Antarctic Winterization Readiness</h3>
                <div className="space-y-2.5 text-xs text-slate-600 dark:text-slate-300">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span>Diesel fuel additives certified (-65°C)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span>BESS heating jacket loops operational</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span>Turbine blade electro-thermal de-icing checked</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span>Freshwater conduit heat tracing armed</span>
                  </div>
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center text-xs">
                <span className="text-slate-500 dark:text-slate-400">Polar Winter Readiness:</span>
                <span className="px-2.5 py-1 rounded font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  100% CERTIFIED
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Dedicated Security & Intrusion Detection System (IDS) Console */}
        <section
          className={`rounded-2xl p-6 transition-all duration-500 border ${isCompromised
            ? "bg-rose-50 dark:bg-[#180d15] border-rose-500/80 shadow-2xl shadow-rose-900/30 red-alert-glow"
            : "bg-white dark:bg-[#0d1525] border-slate-200 dark:border-slate-800 shadow-xl"
            }`}
        >
          {/* Header & Posture Banner */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4 mb-4">
            <div className="flex items-center gap-3">
              <div
                className={`p-2.5 rounded-xl border ${isCompromised
                  ? "bg-rose-500/20 border-rose-500 text-rose-400 animate-pulse"
                  : "bg-emerald-500/10 border-emerald-500/40 text-emerald-400"
                  }`}
              >
                <Shield className="h-6 w-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-black tracking-wide text-slate-900 dark:text-white">
                    Cyber-Physical Intrusion Detection System (IDS)
                  </h2>
                  <span
                    className={`px-3 py-0.5 rounded-full text-xs font-black tracking-wider uppercase ${isCompromised
                      ? "bg-rose-500 text-slate-900 dark:text-white animate-bounce"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                      }`}
                  >
                    POSTURE: {securityStatus?.posture || "SECURE"}
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Real-time heuristics engine monitoring telemetry for Sensor Spoofing, Load Hijacking, and Battery Runaway
                </p>
              </div>
            </div>

            {/* Red Team Attack Simulator & Reset Actions */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mr-1">
                Red Team Simulator:
              </span>
              <button
                onClick={() => handleRedTeamAttack("load-hijack")}
                disabled={loadingAction === "load-hijack"}
                className="px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 flex items-center gap-1.5 transition-all"
              >
                <Flame className="h-3.5 w-3.5" /> Simulate Load Hijack
              </button>
              <button
                onClick={() => handleRedTeamAttack("sensor-spoof")}
                disabled={loadingAction === "sensor-spoof"}
                className="px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 flex items-center gap-1.5 transition-all"
              >
                <Radio className="h-3.5 w-3.5" /> Simulate Sensor Spoof
              </button>
              <button
                onClick={() => handleRedTeamAttack("thermal-runaway")}
                disabled={loadingAction === "thermal-runaway"}
                className="px-3 py-1.5 rounded-lg text-xs font-bold bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/40 flex items-center gap-1.5 transition-all"
              >
                <Activity className="h-3.5 w-3.5" /> Thermal Runaway
              </button>
              <button
                onClick={handleResetPosture}
                disabled={loadingAction === "reset-posture"}
                className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5 transition-all"
              >
                <CheckCircle2 className="h-3.5 w-3.5" /> Reset Posture
              </button>
            </div>
          </div>

          {/* Active Threats Display */}
          {isCompromised && securityStatus?.active_threats?.length > 0 && (
            <div className="mb-4 p-4 rounded-xl bg-rose-950/40 border border-rose-500/60 space-y-2">
              <div className="flex items-center gap-2 text-rose-400 font-bold text-xs uppercase tracking-wide">
                <AlertTriangle className="h-4 w-4" /> Active Intrusion Anomaly Detected!
              </div>
              {securityStatus.active_threats.map((threat: any, i: number) => (
                <div key={i} className="text-xs text-slate-700 dark:text-slate-200">
                  <p className="font-semibold text-rose-300">
                    [{threat.type}] Vector: {threat.channel}
                  </p>
                  <p className="text-slate-600 dark:text-slate-300 text-[11px]">{threat.description}</p>
                  <p className="text-cyan-400 text-[11px] mt-0.5">Automated Grid Response: {threat.mitigation}</p>
                </div>
              ))}
            </div>
          )}

          {/* Intercepted Attacks Audit Log */}
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider mb-2">
              <Terminal className="h-3.5 w-3.5 text-cyan-400" />
              Security Interception &amp; Audit Log
            </div>
            <div className="max-h-40 overflow-y-auto space-y-1.5 bg-slate-200 dark:bg-slate-100/70 dark:bg-slate-950/70 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-[11px] font-mono">
              {(securityStatus?.audit_log || []).map((entry: any, idx: number) => (
                <div key={idx} className="flex items-baseline gap-2 text-slate-500 dark:text-slate-400">
                  <span className="text-slate-500">{entry.timestamp?.slice(11, 19)}Z</span>
                  <span
                    className={`font-bold ${entry.status === "INTERCEPTED" ? "text-rose-400" : "text-emerald-400"
                      }`}
                  >
                    [{entry.status}]
                  </span>
                  <span className="text-slate-600 dark:text-slate-300 font-semibold">{entry.vector}:</span>
                  <span className="text-slate-500 dark:text-slate-400">{entry.details}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
