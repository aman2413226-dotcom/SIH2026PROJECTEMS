"use client";

import React, { useState, useEffect } from "react";
import { ThemeToggle } from "./components/theme-toggle";
import {
  Zap, Sun, Wind, Battery, Fuel, CloudRain, Shield, AlertTriangle, Activity, Flame, Radio, Thermometer, Compass, Terminal, CheckCircle2
} from "lucide-react";

const CircularGauge = ({ 
  value, 
  max = 100, 
  color = "text-cyan-400", 
  label, 
  unit 
}: { 
  value: number, 
  max?: number, 
  color?: string, 
  label: string, 
  unit: string 
}) => {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(value, max) / max) * circumference;

  return (
    <div className="flex flex-col items-center justify-center relative">
      <svg className="w-24 h-24 transform -rotate-90">
        <circle cx="48" cy="48" r={radius} stroke="currentColor" strokeWidth="6" fill="transparent" className="text-slate-200 dark:text-slate-800" />
        <circle 
          cx="48" cy="48" r={radius} stroke="currentColor" strokeWidth="6" fill="transparent" 
          strokeDasharray={circumference} 
          strokeDashoffset={strokeDashoffset} 
          className={`${color} transition-all duration-1000 ease-out`} 
          strokeLinecap="round" 
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className="text-lg font-black text-slate-900 dark:text-white leading-none">{value.toFixed(1)}</span>
        <span className="text-[10px] text-slate-500 font-semibold uppercase">{unit}</span>
      </div>
      <span className="mt-2 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">{label}</span>
    </div>
  );
};

export default function PolarEMSDashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [apiOnline, setApiOnline] = useState(true);
  const [activeStation, setActiveStation] = useState("BHARATI");
  const [bharatiTime, setBharatiTime] = useState<string>("");

  // Telemetry States
  const [telemetry, setTelemetry] = useState<any>(null);
  const [powerFlow, setPowerFlow] = useState<any>(null);
  const [securityStatus, setSecurityStatus] = useState<any>(null);
  const [dispatchData, setDispatchData] = useState<any>(null);
  const [faults, setFaults] = useState<any[]>([]);
  const [emissionStats, setEmissionStats] = useState<any>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const API_BASE = "http://localhost:8000/api/v1";

  // Clock Effect for Bharati Station Time (IST - UTC+5:30)
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = { 
        timeZone: 'Asia/Kolkata', 
        year: 'numeric', month: 'short', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
      };
      setBharatiTime(new Intl.DateTimeFormat('en-GB', options).format(now));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch telemetry every 1.5 seconds
  useEffect(() => {
    let isMounted = true;

    async function pollTelemetry() {
      try {
        const [dashRes, flowRes, secRes, fltRes, emisRes] = await Promise.all([
          fetch(`${API_BASE}/dashboard/overview`).catch(() => null),
          fetch(`${API_BASE}/dashboard/power-flow`).catch(() => null),
          fetch(`${API_BASE}/security/status`).catch(() => null),
          fetch(`${API_BASE}/faults/active`).catch(() => null),
          fetch(`${API_BASE}/emission/stats`).catch(() => null),
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
        
        if (emisRes && emisRes.ok) {
          const emis = await emisRes.json();
          if (isMounted) setEmissionStats(emis);
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
        .catch(() => {});
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
    } catch (e) {}
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
    } catch (e) {}
    setLoadingAction(null);
  };

  const handleResetPosture = async () => {
    setLoadingAction("reset-posture");
    try {
      await fetch(`${API_BASE}/security/reset`, { method: "POST" });
      const secRes = await fetch(`${API_BASE}/security/status`);
      if (secRes.ok) setSecurityStatus(await secRes.json());
    } catch (e) {}
    setLoadingAction(null);
  };

  // Safe fallback values
  const pb = telemetry?.power_balance || { total_load_kw: 112.5, total_generation_kw: 112.5, renewable_fraction_pct: 78.4 };
  const gen = telemetry?.generation_sources || { solar_pv_kw: 28.5, wind_turbines_kw: 54.0, diesel_generators_kw: 30.0 };
  const auto = telemetry?.autonomy || { battery_soc_pct: 78.5, battery_cell_temp_c: 19.5, fuel_reserve_liters: 45200, projected_fuel_days: 72.0 };
  const env = telemetry?.environment || {};
  const isCompromised = securityStatus?.posture === "COMPROMISED";
  const ghi_val = env?.ghi_wm2 !== undefined ? env.ghi_wm2 : 320;

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
              <span className="font-black tracking-wider text-xl bg-gradient-to-r from-slate-800 via-cyan-700 to-cyan-500 dark:from-white dark:via-slate-100 dark:to-cyan-300 bg-clip-text text-transparent">
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
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === "dashboard"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:text-slate-200"
            }`}
          >
            <Activity className="h-3.5 w-3.5" /> Mission Control
          </button>
          <button
            onClick={() => setActiveTab("dispatch")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === "dispatch"
                ? "bg-teal-500/20 text-teal-300 border border-teal-500/40 shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:text-slate-200"
            }`}
          >
            <Zap className="h-3.5 w-3.5" /> 24h AI Dispatch
          </button>
          <button
            onClick={() => setActiveTab("diagnostics")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === "diagnostics"
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
          {/* Station Display */}
          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-1 pr-3">
            <Compass className="h-3.5 w-3.5 text-cyan-400 ml-1" />
            <span className="text-slate-700 dark:text-slate-200 font-semibold text-xs">
              Bharati Station (Larsemann)
            </span>
          </div>

          {/* Meteorological Badges */}
          <div className="hidden lg:flex items-center gap-2">
            <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-cyan-300 flex items-center gap-1.5">
              <Thermometer className="h-3.5 w-3.5 text-cyan-400" />
              <b>{telemetry?.environment?.ambient_temp_c?.toFixed(1) || "-52.4"}°C</b>
              <span className="text-[10px] text-slate-500 dark:text-slate-400">(Chill: {telemetry?.environment?.wind_chill_c?.toFixed(1) || "-65.2"}°C)</span>
            </span>
            <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-teal-300 flex items-center gap-1.5">
              <Wind className="h-3.5 w-3.5 text-teal-400" />
              <b>{env?.wind_speed_ms?.toFixed(1) || "14.8"} m/s</b>
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Katabatic</span>
            </span>
            <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-amber-300 flex items-center gap-1.5">
              <Sun className="h-3.5 w-3.5 text-amber-400" />
              <b>{ghi_val.toFixed(0)} W/m²</b>
              {ghi_val === 0 && <span className="text-[10px] text-slate-500 dark:text-slate-400">(Night)</span>}
            </span>
            <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-300 flex items-center gap-1.5 font-mono">
              🕐 <b>{bharatiTime || "..."}</b>
              <span className="text-[10px] text-cyan-500 font-bold">IST</span>
            </span>
          </div>

          {/* Online Indicator */}
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-100/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
            <span
              className={`h-2 w-2 rounded-full ${
                apiOnline ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
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
      <main className="flex-1 p-6 space-y-6 max-w-[1700px] w-full mx-auto relative">
        
        {/* Subtle background grid pattern */}
        <div className="absolute inset-0 pointer-events-none opacity-20 dark:opacity-40" style={{ backgroundImage: 'linear-gradient(rgba(56, 189, 248, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(56, 189, 248, 0.1) 1px, transparent 1px)', backgroundSize: '30px 30px' }}></div>
        
        {/* KPI Telemetry Stat Cards - SCADA Gauges */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 relative z-10">
          
          {/* 1. Station Demand */}
          <div className="scada-glass rounded-xl p-4 flex flex-col items-center">
            <div className="w-full flex justify-between items-center mb-2">
              <Zap className="h-4 w-4 text-cyan-500" />
              <span className="text-[10px] font-mono text-cyan-600 dark:text-cyan-400 uppercase">SYS_LD_01</span>
            </div>
            <CircularGauge value={pb.total_load_kw !== undefined ? pb.total_load_kw : 0} max={160} color="text-cyan-500" label="Station Demand" unit="kW" />
            <div className="w-full mt-3 flex justify-between text-[10px] border-t border-slate-200 dark:border-slate-800 pt-2 font-mono text-slate-500">
              <span>THERMAL HTG:</span>
              <span className="text-cyan-600 dark:text-cyan-400 font-bold">{telemetry?.consumption_breakdown?.life_support_heating_kw?.toFixed(1) || "--"} kW</span>
            </div>
          </div>

          {/* 2. Renewable Output */}
          <div className="scada-glass rounded-xl p-4 flex flex-col items-center">
            <div className="w-full flex justify-between items-center mb-2">
              <Sun className="h-4 w-4 text-emerald-500" />
              <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 uppercase">GEN_RN_02</span>
            </div>
            <CircularGauge value={(gen.solar_pv_kw || 0) + (gen.wind_turbines_kw || 0)} max={160} color="text-emerald-500" label="Renewable Gen" unit="kW" />
            <div className="w-full mt-3 flex justify-between text-[10px] border-t border-slate-200 dark:border-slate-800 pt-2 font-mono text-slate-500">
              <span>PENETRATION:</span>
              <span className="text-emerald-600 dark:text-emerald-400 font-bold">{pb.renewable_fraction_pct?.toFixed(1) || "--"}%</span>
            </div>
          </div>

          {/* 3. BESS SOC */}
          <div className="scada-glass rounded-xl p-4 flex flex-col items-center">
            <div className="w-full flex justify-between items-center mb-2">
              <Battery className="h-4 w-4 text-blue-500" />
              <span className="text-[10px] font-mono text-blue-600 dark:text-blue-400 uppercase">BESS_ST_03</span>
            </div>
            <CircularGauge value={auto.battery_soc_pct || 0} max={100} color="text-blue-500" label="Battery SOC" unit="%" />
            <div className="w-full mt-3 flex justify-between text-[10px] border-t border-slate-200 dark:border-slate-800 pt-2 font-mono text-slate-500">
              <span>CORE TEMP:</span>
              <span className="text-blue-600 dark:text-blue-400 font-bold">{auto.battery_cell_temp_c?.toFixed(1) || "--"}°C</span>
            </div>
          </div>

          {/* 4. Diesel Reserve */}
          <div className="scada-glass rounded-xl p-4 flex flex-col items-center">
            <div className="w-full flex justify-between items-center mb-2">
              <Fuel className="h-4 w-4 text-amber-500" />
              <span className="text-[10px] font-mono text-amber-600 dark:text-amber-400 uppercase">DSL_RS_04</span>
            </div>
            <CircularGauge value={(auto.fuel_reserve_liters || 0) / 1000} max={50} color="text-amber-500" label="Diesel Rsv (kL)" unit="kL" />
            <div className="w-full mt-3 flex justify-between text-[10px] border-t border-slate-200 dark:border-slate-800 pt-2 font-mono text-slate-500">
              <span>ENDURANCE:</span>
              <span className="text-amber-600 dark:text-amber-400 font-bold">{auto.projected_fuel_days?.toFixed(1) || "--"} DAYS</span>
            </div>
          </div>

          {/* 5. Carbon Emissions */}
          <div className="scada-glass rounded-xl p-4 flex flex-col items-center">
            <div className="w-full flex justify-between items-center mb-2">
              <CloudRain className="h-4 w-4 text-rose-500" />
              <span className="text-[10px] font-mono text-rose-600 dark:text-rose-400 uppercase">EMI_TR_05</span>
            </div>
            <CircularGauge value={emissionStats?.co2_emission_rate_kg_per_hour || 0} max={100} color="text-rose-500" label="CO2 Output" unit="kg/h" />
            <div className="w-full mt-3 flex justify-between text-[10px] border-t border-slate-200 dark:border-slate-800 pt-2 font-mono text-slate-500">
              <span>CUMULATIVE:</span>
              <span className="text-rose-600 dark:text-rose-400 font-bold">{emissionStats?.cumulative_co2_tonnes?.toFixed(2) || "--"} t</span>
            </div>
          </div>
        </section>

        {/* Tab 1: Dashboard & Power Flow */}
        {activeTab === "dashboard" && (
          <div className="grid grid-cols-1 gap-6 relative z-10">
            {/* Interactive Animated Power Flow Diagram */}
            <div className="scada-glass rounded-2xl p-6 relative flex flex-col">
              <div className="flex flex-wrap items-center justify-between mb-6 border-b border-slate-200/50 dark:border-slate-800/80 pb-4">
                <div>
                  <h2 className="text-lg font-black text-slate-900 dark:text-white flex items-center gap-2 uppercase tracking-wide">
                    <Activity className="h-5 w-5 text-cyan-500" />
                    Microgrid Power Flow SCADA
                  </h2>
                  <p className="text-xs font-mono text-slate-500 dark:text-slate-400 mt-1">
                    [REAL-TIME] Bidirectional AC/DC synchronization map
                  </p>
                </div>
                <span className="px-3 py-1.5 rounded bg-cyan-500/10 text-[11px] font-mono font-bold text-cyan-600 dark:text-cyan-400 border border-cyan-500/30 glow-cyan">
                  {pb.total_generation_kw !== undefined ? "GRID SYNC: ONLINE" : "GRID SYNC: PENDING"}
                </span>
              </div>

              {/* Power Flow SVG Visualization */}
              <div className="flex-1 min-h-[380px] relative rounded-xl scada-glass-panel flex items-center justify-center p-4">
                <svg className="w-full h-full max-h-[350px]" viewBox="0 0 800 320" fill="none">
                  {/* Flow Paths - Animated */}
                  {/* Solar to Central Bus */}
                  <path d="M 160 60 L 380 160" stroke="rgba(245, 158, 11, 0.4)" strokeWidth="6" />
                  {gen.solar_pv_kw > 0 && <path d="M 160 60 L 380 160" stroke="#f59e0b" strokeWidth="3" className="flow-anim" />}
                  
                  {/* Wind to Central Bus */}
                  <path d="M 160 160 L 380 160" stroke="rgba(16, 185, 129, 0.4)" strokeWidth="6" />
                  {gen.wind_turbines_kw > 0 && <path d="M 160 160 L 380 160" stroke="#10b981" strokeWidth="3" className="flow-anim" />}
                  
                  {/* Diesel to Central Bus */}
                  <path d="M 160 260 L 380 160" stroke="rgba(244, 63, 94, 0.4)" strokeWidth="6" />
                  {gen.diesel_generators_kw > 0 && <path d="M 160 260 L 380 160" stroke="#f43f5e" strokeWidth="3" className="flow-anim" />}

                  {/* Central Bus to BESS (bidirectional) */}
                  <path d="M 420 160 L 640 80" stroke="rgba(56, 189, 248, 0.4)" strokeWidth="6" />
                  <path d="M 420 160 L 640 80" stroke="#38bdf8" strokeWidth="3" className="flow-anim opacity-90" />
                  
                  {/* Central Bus to Station Loads */}
                  <path d="M 420 160 L 640 240" stroke="rgba(168, 85, 247, 0.4)" strokeWidth="6" />
                  <path d="M 420 160 L 640 240" stroke="#a855f7" strokeWidth="3" className="flow-anim opacity-90" />

                  {/* Generation Nodes */}
                  <g transform="translate(40, 30)">
                    <rect width="120" height="60" rx="4" className="fill-slate-100 dark:fill-slate-900/80" stroke="#f59e0b" strokeWidth="2" />
                    <text x="60" y="24" className="fill-slate-500 dark:fill-slate-300" fontSize="10" fontFamily="monospace" fontWeight="bold" textAnchor="middle">SOLAR PV</text>
                    <text x="60" y="46" className="fill-amber-600 dark:fill-amber-400" fontSize="16" fontFamily="monospace" fontWeight="black" textAnchor="middle">{gen.solar_pv_kw?.toFixed(1) || "0.0"} kW</text>
                  </g>

                  <g transform="translate(40, 130)">
                    <rect width="120" height="60" rx="4" className="fill-slate-100 dark:fill-slate-900/80" stroke="#10b981" strokeWidth="2" />
                    <text x="60" y="24" className="fill-slate-500 dark:fill-slate-300" fontSize="10" fontFamily="monospace" fontWeight="bold" textAnchor="middle">WIND FARM</text>
                    <text x="60" y="46" className="fill-emerald-600 dark:fill-emerald-400" fontSize="16" fontFamily="monospace" fontWeight="black" textAnchor="middle">{gen.wind_turbines_kw?.toFixed(1) || "0.0"} kW</text>
                  </g>

                  <g transform="translate(40, 230)">
                    <rect width="120" height="60" rx="4" className="fill-slate-100 dark:fill-slate-900/80" stroke={gen.diesel_generators_kw > 0 ? "#f43f5e" : "#475569"} strokeWidth="2" />
                    <text x="60" y="24" className="fill-slate-500 dark:fill-slate-300" fontSize="10" fontFamily="monospace" fontWeight="bold" textAnchor="middle">DIESEL GEN</text>
                    <text x="60" y="46" fill={gen.diesel_generators_kw > 0 ? "#fb7185" : "#64748b"} fontSize="16" fontFamily="monospace" fontWeight="black" textAnchor="middle">{gen.diesel_generators_kw?.toFixed(1) || "0.0"} kW</text>
                  </g>

                  {/* Central Bus Node */}
                  <g transform="translate(340, 110)">
                    <rect width="120" height="100" rx="6" className="fill-slate-100/90 dark:fill-slate-900/90 glow-cyan" stroke="#38bdf8" strokeWidth="3" />
                    <text x="60" y="28" className="fill-slate-600 dark:fill-slate-400" fontSize="10" fontFamily="monospace" fontWeight="bold" textAnchor="middle">MAIN BUS</text>
                    <text x="60" y="54" className="fill-cyan-600 dark:fill-cyan-400" fontSize="20" fontFamily="monospace" fontWeight="black" textAnchor="middle">{pb.total_generation_kw?.toFixed(1) || "0.0"} kW</text>
                    <rect x="20" y="70" width="80" height="12" rx="2" className="fill-cyan-500/20" />
                    <text x="60" y="80" className="fill-cyan-700 dark:fill-cyan-400" fontSize="9" fontFamily="monospace" fontWeight="bold" textAnchor="middle">50.02Hz | 400V</text>
                  </g>

                  {/* BESS Node */}
                  <g transform="translate(640, 40)">
                    <rect width="130" height="80" rx="4" className="fill-slate-100 dark:fill-slate-900/80" stroke="#38bdf8" strokeWidth="2" />
                    <text x="65" y="24" className="fill-slate-500 dark:fill-slate-300" fontSize="10" fontFamily="monospace" fontWeight="bold" textAnchor="middle">BESS STORAGE</text>
                    <text x="65" y="48" className="fill-cyan-600 dark:fill-cyan-400" fontSize="18" fontFamily="monospace" fontWeight="black" textAnchor="middle">SOC {auto.battery_soc_pct?.toFixed(1) || "0.0"}%</text>
                    <text x="65" y="66" className="fill-slate-600 dark:fill-slate-400" fontSize="10" fontFamily="monospace" textAnchor="middle">{auto.battery_cell_temp_c?.toFixed(1) || "0.0"}°C CORE</text>
                  </g>

                  {/* Station Loads Node */}
                  <g transform="translate(640, 195)">
                    <rect 
                      width="130" height="85" rx="4" 
                      className={`fill-slate-100 dark:fill-slate-900/80 ${isCompromised ? "red-alert-glow" : ""}`}
                      stroke={isCompromised ? "#f43f5e" : "#a855f7"} 
                      strokeWidth={isCompromised ? "3" : "2"} 
                    />
                    <text x="65" y="24" className="fill-slate-500 dark:fill-slate-300" fontSize="10" fontFamily="monospace" fontWeight="bold" textAnchor="middle">STATION LOADS</text>
                    <text x="65" y="52" fill={isCompromised ? "#f43f5e" : "#c084fc"} fontSize="20" fontFamily="monospace" fontWeight="black" textAnchor="middle">{pb.total_load_kw?.toFixed(1) || "0.0"} kW</text>
                    <text x="65" y="70" fill={isCompromised ? "#f43f5e" : "#94a3b8"} fontSize="9" fontFamily="monospace" textAnchor="middle">
                      {isCompromised ? "OVERLOAD ANOMALY" : "LIFE SUPPORT NOMINAL"}
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
                <h2 className="text-lg font-bold text-slate-900 dark:white flex items-center gap-2">
                  <Zap className="h-5 w-5 text-teal-400" />
                  24-Hour Multi-Objective Microgrid Dispatch Schedule
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  LightGBM seasonal load predictions optimized to minimize diesel runtime and protect BESS health
                </p>
              </div>
              <div className="flex gap-4 text-xs font-semibold">
                <span className="px-3 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300">
                  Expected 24h Fuel: <b>{dispatchData?.expected_24h_fuel_liters !== undefined ? dispatchData.expected_24h_fuel_liters : "--"} L</b>
                </span>
                <span className="px-3 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300">
                  Emissions: <b>{dispatchData?.expected_24h_emissions_co2_kg !== undefined ? dispatchData.expected_24h_emissions_co2_kg : "--"} kg CO₂</b>
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
          className={`rounded-2xl p-6 transition-all duration-500 relative z-10 ${
            isCompromised ? "scada-glass-alert" : "scada-glass"
          }`}
        >
          {/* Header & Posture Banner */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200/50 dark:border-slate-800/80 pb-4 mb-4">
            <div className="flex items-center gap-4">
              <div
                className={`p-3 rounded-lg border ${
                  isCompromised
                    ? "bg-rose-500/20 border-rose-500 text-rose-400 animate-pulse"
                    : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                }`}
              >
                <Shield className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-lg font-black tracking-widest uppercase text-slate-900 dark:text-white flex items-center gap-3">
                  CYBER-PHYSICAL IDS
                  <span
                    className={`px-3 py-1 rounded text-xs font-mono font-bold tracking-widest ${
                      isCompromised
                        ? "bg-rose-500 text-white animate-bounce shadow-[0_0_15px_rgba(244,63,94,0.6)]"
                        : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 glow-cyan"
                    }`}
                  >
                    POSTURE: {securityStatus?.posture || "SECURE"}
                  </span>
                </h2>
                <p className="text-[11px] font-mono text-slate-500 dark:text-slate-400 mt-1 uppercase">
                  Zero-Trust Heuristics Engine running. Monitoring grid telemetry vectors.
                </p>
              </div>
            </div>

            {/* Red Team Attack Simulator & Reset Actions */}
            <div className="flex flex-wrap items-center gap-2 bg-slate-100/80 dark:bg-slate-900/60 p-2 rounded-xl border border-slate-300/50 dark:border-slate-700/50 backdrop-blur-md shadow-inner">
              <span className="text-[10px] font-mono font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mr-2 ml-1">
                Red Team Sim:
              </span>
              <button
                onClick={() => handleRedTeamAttack("load-hijack")}
                disabled={loadingAction === "load-hijack"}
                className="px-4 py-2 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-gradient-to-b from-white to-slate-100 dark:from-slate-700 dark:to-slate-800 hover:from-rose-100 hover:to-rose-200 dark:hover:from-rose-500 dark:hover:to-rose-700 text-slate-700 dark:text-slate-300 hover:text-rose-800 dark:hover:text-white border border-slate-300 dark:border-slate-600 hover:border-rose-400 transition-all shadow-md active:translate-y-px"
              >
                Load Hijack
              </button>
              <button
                onClick={() => handleRedTeamAttack("sensor-spoof")}
                disabled={loadingAction === "sensor-spoof"}
                className="px-4 py-2 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-gradient-to-b from-white to-slate-100 dark:from-slate-700 dark:to-slate-800 hover:from-amber-100 hover:to-amber-200 dark:hover:from-amber-500 dark:hover:to-amber-700 text-slate-700 dark:text-slate-300 hover:text-amber-800 dark:hover:text-white border border-slate-300 dark:border-slate-600 hover:border-amber-400 transition-all shadow-md active:translate-y-px"
              >
                Sensor Spoof
              </button>
              <button
                onClick={() => handleRedTeamAttack("thermal-runaway")}
                disabled={loadingAction === "thermal-runaway"}
                className="px-4 py-2 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-gradient-to-b from-white to-slate-100 dark:from-slate-700 dark:to-slate-800 hover:from-purple-100 hover:to-purple-200 dark:hover:from-purple-500 dark:hover:to-purple-700 text-slate-700 dark:text-slate-300 hover:text-purple-800 dark:hover:text-white border border-slate-300 dark:border-slate-600 hover:border-purple-400 transition-all shadow-md active:translate-y-px"
              >
                Runaway
              </button>
              <button
                onClick={handleResetPosture}
                disabled={loadingAction === "reset-posture"}
                className="px-4 py-2 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-gradient-to-b from-white to-slate-100 dark:from-slate-700 dark:to-slate-800 hover:from-emerald-100 hover:to-emerald-200 dark:hover:from-emerald-500 dark:hover:to-emerald-700 text-slate-700 dark:text-slate-300 hover:text-emerald-800 dark:hover:text-white border border-slate-300 dark:border-slate-600 hover:border-emerald-400 transition-all shadow-md active:translate-y-px ml-2"
              >
                Reset Posture
              </button>
            </div>
          </div>

          {/* Active Threats Display */}
          {isCompromised && securityStatus?.active_threats?.length > 0 && (
            <div className="mb-4 p-4 rounded bg-rose-950/80 border-l-4 border-rose-500 shadow-inner">
              <div className="flex items-center gap-2 text-rose-400 font-mono font-bold text-[11px] uppercase tracking-widest mb-2">
                <AlertTriangle className="h-4 w-4" /> [CRITICAL] Anomaly Detected
              </div>
              {securityStatus.active_threats.map((threat: any, i: number) => (
                <div key={i} className="text-xs font-mono pl-6 border-l-2 border-rose-500/30 py-1 mb-2">
                  <p className="text-rose-300 font-bold mb-1">VECTOR: {threat.channel} ({threat.type})</p>
                  <p className="text-slate-300 opacity-90">{threat.description}</p>
                  <p className="text-cyan-400 mt-1">&gt; MITIGATION: {threat.mitigation}</p>
                </div>
              ))}
            </div>
          )}

          {/* Intercepted Attacks Audit Log - Terminal Style */}
          <div className="mt-6">
            <div className="flex items-center gap-2 text-[10px] font-mono font-bold text-cyan-500 uppercase tracking-widest mb-2">
              <Terminal className="h-4 w-4" />
              IDS Terminal Log
            </div>
            <div className="h-48 overflow-y-auto bg-black border border-slate-800 p-4 rounded-lg shadow-inner font-mono text-[11px]">
              {(securityStatus?.audit_log || []).map((entry: any, idx: number) => (
                <div key={idx} className="flex gap-3 mb-1.5 opacity-90 hover:opacity-100 transition-opacity">
                  <span className="text-slate-500 shrink-0">[{entry.timestamp?.slice(11, 19)}]</span>
                  <span
                    className={`shrink-0 font-bold ${
                      entry.status === "INTERCEPTED" ? "text-rose-500" : "text-emerald-500"
                    }`}
                  >
                    {entry.status === "INTERCEPTED" ? "[BLOCKED]" : "[CLEARED]"}
                  </span>
                  <span className="text-slate-300">
                    <span className="text-cyan-600 font-bold">{entry.vector}</span> &mdash; {entry.details}
                  </span>
                </div>
              ))}
              {(!securityStatus?.audit_log || securityStatus.audit_log.length === 0) && (
                <div className="text-slate-600 italic">No intrusions logged. Awaiting telemetry...</div>
              )}
              {/* Blinking cursor */}
              <div className="mt-2 text-cyan-500 animate-pulse">_</div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
