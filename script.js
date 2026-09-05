/* ===========================================================
   PolarEMS — Antarctic Microgrid Energy Management & Digital Twin
   All telemetry below is simulated for demonstration. Swap
   readSensors() for a real feed to go live — everything else
   (classification, alarms, charts) works unchanged.
=========================================================== */

const STATION = {
    batteryCapacityKwh: 500,
    fuelCapacityL: 15000,
    solarMaxKw: 60,
    windMaxKw: 90,
    gensetMaxKw: 80,
};

const SCENARIOS = [
    { id: "clear", label: "Clear · midnight sun", tempC: -8, windSpeed: 8, cloud: 0.05, daylight: 1.0, demandScale: 1.0 },
    { id: "overcast", label: "Overcast", tempC: -14, windSpeed: 11, cloud: 0.6, daylight: 1.0, demandScale: 1.05 },
    { id: "polar-night", label: "Polar night · steady wind", tempC: -24, windSpeed: 13, cloud: 1.0, daylight: 0.0, demandScale: 1.1 },
    { id: "calm-night", label: "Polar night · calm", tempC: -31, windSpeed: 3, cloud: 1.0, daylight: 0.0, demandScale: 1.15 },
    { id: "blizzard", label: "Blizzard · turbine cutout", tempC: -19, windSpeed: 27, cloud: 1.0, daylight: 0.2, demandScale: 1.25 },
];

const state = {
    scenario: SCENARIOS[0],
    simTime: new Date("2026-09-01T21:43:06Z"),
    speedMultiplier: 1,
    paused: false,
    batterySoc: 82.5,
    fuelLiters: 14200,
    gensetOnline: true,
    manualLoad: 125.5,
    serviceHoursRemaining: 579.5,
    co2CumulativeTonnes: 12.4,
    timer: null,
};

function round1(n) { return Math.round(n * 10) / 10; }
function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }

/* ---------- Sensor model ---------- */
function readSensors() {
    const sc = state.scenario;
    const jitter = (spread) => (Math.random() - 0.5) * spread;

    const solarPotential = STATION.solarMaxKw * sc.daylight * (1 - sc.cloud * 0.85);
    const solarKw = Math.max(0, solarPotential + jitter(2));

    const cutout = sc.windSpeed >= 25;
    const windRatio = Math.min(1, sc.windSpeed / 16);
    const windKw = cutout ? Math.max(0, 3 + jitter(1)) : Math.max(0, STATION.windMaxKw * windRatio * 0.75 + jitter(3));

    const baseLoadKw = Math.max(20, 78 * sc.demandScale + jitter(3));
    const irradiance = Math.round(solarPotential > 0 ? 200 + solarPotential * 6 + jitter(15) : jitter(4));

    return {
        solarKw: round1(solarKw),
        windKw: round1(windKw),
        baseLoadKw: round1(baseLoadKw),
        irradiance: Math.max(0, irradiance),
        tempC: sc.tempC + jitter(0.5),
        windSpeed: sc.windSpeed,
        turbineCutout: cutout,
    };
}

/* ---------- Storage / genset dynamics ---------- */
function stepPower(sensors, hoursElapsed) {
    const effectiveLoad = state.manualLoad != null ? state.manualLoad : sensors.baseLoadKw;
    const renewableKw = sensors.solarKw + sensors.windKw;
    const chargeTarget = state.batterySoc < 98 ? 4.5 : 0;

    let dieselKw = 0;
    if (state.gensetOnline) {
        dieselKw = clamp(effectiveLoad + chargeTarget - renewableKw, 0, STATION.gensetMaxKw);
    }

    const batteryNetKw = renewableKw + dieselKw - effectiveLoad;
    const batteryKwh = STATION.batteryCapacityKwh * (state.batterySoc / 100);
    const newBatteryKwh = clamp(batteryKwh + batteryNetKw * hoursElapsed,
        STATION.batteryCapacityKwh * 0.02, STATION.batteryCapacityKwh);
    state.batterySoc = newBatteryKwh / STATION.batteryCapacityKwh * 100;

    if (dieselKw > 0) {
        state.fuelLiters = clamp(state.fuelLiters - dieselKw * hoursElapsed * 0.3, 0, STATION.fuelCapacityL);
        state.serviceHoursRemaining = Math.max(0, state.serviceHoursRemaining - hoursElapsed);
    }

    const co2RateKgH = dieselKw * 0.728;
    state.co2CumulativeTonnes += co2RateKgH * hoursElapsed / 1000;

    const penetration = renewableKw + dieselKw > 0 ? (renewableKw / (renewableKw + dieselKw)) * 100 : 100;
    const thermalLoad = effectiveLoad * 0.677;

    return { effectiveLoad, renewableKw, dieselKw, batteryNetKw, co2RateKgH, penetration, thermalLoad };
}

/* ---------- Alarm engine ---------- */
let alarmSeq = 0;
function nextAlarmCode() { alarmSeq += 1; return `ALT-${String(alarmSeq).padStart(3, "0")}`; }

function buildAlarms(sensors, derived) {
    const alarms = [];

    if (sensors.turbineCutout) {
        alarms.push({
            sev: "warning", component: "WIND_TURBINE_1",
            message: "Sustained wind exceeds 25 m/s safety cutout; blades feathered automatically."
        });
    } else if (sensors.tempC < -15) {
        alarms.push({
            sev: "warning", component: "WIND_TURBINE_1",
            message: "Minor rotor icing detected; anti-icing heater activated."
        });
    }

    if (state.batterySoc < 20) {
        alarms.push({
            sev: "critical", component: "BESS_STORAGE",
            message: `State of charge at ${state.batterySoc.toFixed(1)}% — approaching low-voltage protection limit.`
        });
    } else if (state.batterySoc < 35) {
        alarms.push({
            sev: "warning", component: "BESS_STORAGE",
            message: `State of charge at ${state.batterySoc.toFixed(1)}% — below optimal reserve band.`
        });
    }

    const fuelRatio = state.fuelLiters / STATION.fuelCapacityL;
    if (fuelRatio < 0.15) {
        alarms.push({
            sev: "critical", component: "DIESEL_GENSET",
            message: `Reserve at ${Math.round(state.fuelLiters).toLocaleString()} L (${Math.round(fuelRatio * 100)}%) — below resupply threshold.`
        });
    } else if (fuelRatio < 0.3) {
        alarms.push({
            sev: "warning", component: "DIESEL_GENSET",
            message: `Reserve at ${Math.round(state.fuelLiters).toLocaleString()} L (${Math.round(fuelRatio * 100)}%) — schedule resupply.`
        });
    }

    if (!state.gensetOnline && derived.batteryNetKw < -1) {
        alarms.push({
            sev: "critical", component: "DIESEL_GENSET",
            message: "Genset offline while renewable generation is insufficient to meet demand — battery is covering the deficit."
        });
    }

    if (state.serviceHoursRemaining < 50) {
        alarms.push({
            sev: "warning", component: "DIESEL_GENSET",
            message: `Scheduled maintenance due in ${state.serviceHoursRemaining.toFixed(1)} hrs.`
        });
    }

    if (derived.effectiveLoad > 165) {
        alarms.push({
            sev: "warning", component: "STATION_LOAD",
            message: `Demand at ${derived.effectiveLoad.toFixed(1)} kW is well above nominal baseline.`
        });
    }

    return alarms.map((a) => ({ ...a, code: nextAlarmCode() }));
}

/* ---------- 24h dispatch synthesis ---------- */
function buildDispatch(sc) {
    const points = [];
    let totalFuelL = 0, totalCo2Kg = 0;
    for (let h = 0; h <= 24; h++) {
        const solarPotential = STATION.solarMaxKw * sc.daylight * (1 - sc.cloud * 0.85)
            * (sc.daylight === 1 ? 0.8 + 0.2 * Math.max(0, Math.sin((h / 24) * Math.PI * 2)) : 1);
        const windKw = sc.windSpeed >= 25 ? 3 : STATION.windMaxKw * Math.min(1, sc.windSpeed / 16) * 0.75;
        const loadKw = 78 * sc.demandScale * (1 + 0.15 * Math.sin((h / 24) * Math.PI * 2 - 1));
        const solarKw = Math.max(0, solarPotential);
        const renewableKw = solarKw + windKw;
        const battAssistKw = Math.min(Math.max(0, loadKw - renewableKw), 15);
        const dieselKw = Math.max(0, loadKw - renewableKw - battAssistKw);
        totalFuelL += dieselKw * 0.3;
        totalCo2Kg += dieselKw * 0.728;
        points.push({ h, solarKw: round1(solarKw), windKw: round1(windKw), battAssistKw: round1(battAssistKw), dieselKw: round1(dieselKw) });
    }
    const costPerLiter = 1.65, costPerKwhFromGrid = 0; // isolated microgrid — cost is fuel + a small O&M factor
    const totalCost = totalFuelL * costPerLiter + totalCo2Kg * 0.02;
    return { points, totalFuelL: round1(totalFuelL), totalCo2Kg: round1(totalCo2Kg), totalCost: Math.round(totalCost * 100) / 100 };
}

/* ===========================================================
   Rendering
=========================================================== */
function renderTopbar(sensors) {
    document.getElementById("wxTemp").textContent = `${sensors.tempC.toFixed(1)}\u00B0C`;
    document.getElementById("wxWind").textContent = `${sensors.windSpeed.toFixed(1)} m/s`;
    document.getElementById("wxIrr").textContent = `${sensors.irradiance} W/m\u00B2`;
    const t = state.simTime;
    const pad = (n) => String(n).padStart(2, "0");
    document.getElementById("simClock").textContent =
        `${t.getUTCFullYear()}-${pad(t.getUTCMonth() + 1)}-${pad(t.getUTCDate())} ${pad(t.getUTCHours())}:${pad(t.getUTCMinutes())}:${pad(t.getUTCSeconds())} UTC`;
}

function renderStatRow(sensors, derived) {
    document.getElementById("statDemand").textContent = derived.effectiveLoad.toFixed(1);
    document.getElementById("statThermal").textContent = Math.round(derived.thermalLoad);

    document.getElementById("statRenewable").textContent = derived.renewableKw.toFixed(1);
    document.getElementById("statPenetration").textContent = `${Math.round(derived.penetration)}%`;
    document.getElementById("barPenetration").style.width = `${clamp(derived.penetration, 3, 100)}%`;

    document.getElementById("statSoc").textContent = state.batterySoc.toFixed(0);
    const deltaEl = document.getElementById("statSocDelta");
    deltaEl.textContent = `${derived.batteryNetKw >= 0 ? "+" : ""}${derived.batteryNetKw.toFixed(1)} kW`;
    deltaEl.style.color = derived.batteryNetKw >= 0 ? "var(--green)" : "var(--rose)";
    deltaEl.style.background = derived.batteryNetKw >= 0 ? "var(--green-soft)" : "var(--rose-soft)";
    document.getElementById("statBattTemp").textContent = `${(4 + sensors.tempC * -0.05).toFixed(1)}\u00B0C`;
    document.getElementById("barSoc").style.width = `${clamp(state.batterySoc, 2, 100)}%`;

    document.getElementById("statFuel").textContent = Math.round(state.fuelLiters).toLocaleString();
    document.getElementById("statGensetOutput").textContent = derived.dieselKw.toFixed(0);
    document.getElementById("barFuel").style.width = `${clamp(state.fuelLiters / STATION.fuelCapacityL * 100, 2, 100)}%`;

    document.getElementById("statCo2").textContent = derived.co2RateKgH.toFixed(1);
    document.getElementById("statCo2Cum").textContent = state.co2CumulativeTonnes.toFixed(1);
}

function renderFlowMap(sensors, derived) {
    const holder = document.getElementById("flowMap");
    holder.innerHTML = `
    <div class="flow-nodes">
      <div class="flow-line"></div>

      <div class="flow-node" data-n="solar">
        <div class="node-icon" style="background:var(--teal-soft);color:var(--teal)">&#9728;&#65039;</div>
        <div class="node-name">Solar PV Array</div>
        <div class="node-value" style="color:var(--teal)">${sensors.solarKw.toFixed(0)} kW</div>
        <div class="node-foot">+15% Snow Albedo</div>
      </div>

      <div class="flow-node" data-n="wind">
        <div class="node-icon" style="background:var(--violet-soft);color:var(--violet)">&#8767;</div>
        <div class="node-name">Wind Turbines</div>
        <div class="node-value" style="color:var(--violet)">${sensors.windKw.toFixed(0)} kW</div>
        <div class="node-foot">${sensors.turbineCutout ? "Cutout — feathered" : "Anti-Icing Active"}</div>
      </div>

      <div class="flow-node center" data-n="load">
        <span class="bus-pill">AC POWER BUS</span>
        <div class="node-icon" style="background:#fff;color:var(--text-900);box-shadow:0 0 0 2px var(--teal)">&#9889;</div>
        <div class="node-name">Station Load</div>
        <div class="node-value" style="font-size:19px">${derived.effectiveLoad.toFixed(1)} kW</div>
        <div class="node-foot">Thermal: ${Math.round(derived.thermalLoad)} kW</div>
      </div>

      <div class="flow-node" data-n="battery">
        <div class="node-icon" style="background:var(--blue-soft);color:var(--blue)">&#128267;</div>
        <div class="node-name">BESS Storage</div>
        <div class="node-value" style="color:var(--blue)">${state.batterySoc.toFixed(1)}%</div>
        <div class="node-foot">${derived.batteryNetKw >= 0 ? "Charging" : "Discharging"} ${Math.abs(derived.batteryNetKw).toFixed(1)}kW</div>
      </div>

      <div class="flow-node" data-n="diesel">
        <div class="node-icon" style="background:var(--amber-soft);color:var(--amber)">&#9981;</div>
        <div class="node-name">Diesel Genset</div>
        <div class="node-value" style="color:var(--amber)">${derived.dieselKw.toFixed(0)} kW</div>
        <div class="node-foot">Fuel: ${Math.round(state.fuelLiters).toLocaleString()}L</div>
      </div>
    </div>
  `;
}

function renderTwinControls() {
    document.getElementById("btnPause").innerHTML = state.paused ? "&#9654; PLAY" : "&#10074;&#10074; PAUSE";
    document.getElementById("runningPill").textContent = state.paused ? "PAUSED" : "RUNNING LIVE";
    document.getElementById("runningPill").className = state.paused ? "pill pill-amber" : "pill pill-green";
    document.getElementById("speedHint").textContent = `${state.speedMultiplier}x Real\u2011Time`;

    const gensetBtn = document.getElementById("gensetToggle");
    gensetBtn.textContent = state.gensetOnline ? "ONLINE (ACTIVE)" : "OFFLINE";
    gensetBtn.classList.toggle("offline", !state.gensetOnline);

    const slider = document.getElementById("loadSlider");
    if (document.activeElement !== slider) slider.value = state.manualLoad;
    document.getElementById("loadSliderValue").textContent = `${Number(slider.value).toFixed(1)} kW`;
}

function renderSpeedButtons() {
    const holder = document.getElementById("speedButtons");
    holder.innerHTML = "";
    [1, 2, 5, 10].forEach((s) => {
        const btn = document.createElement("button");
        btn.className = "speed-btn" + (s === state.speedMultiplier ? " active" : "");
        btn.textContent = `${s}x`;
        btn.addEventListener("click", () => { state.speedMultiplier = s; restartTimer(); renderSpeedButtons(); renderTwinControls(); });
        holder.appendChild(btn);
    });
}

function renderAlarms(alarms) {
    const list = document.getElementById("alarmList");
    document.getElementById("alarmCountPill").textContent = `${alarms.length} ACTIVE ALARM${alarms.length === 1 ? "" : "S"}`;
    list.innerHTML = "";

    if (alarms.length === 0) {
        const li = document.createElement("li");
        li.className = "alarm-empty";
        li.textContent = "No active alarms — all systems within nominal range.";
        list.appendChild(li);
    } else {
        const glyph = { critical: "&#128993;", warning: "&#9888;\uFE0F", info: "&#8505;\uFE0F" };
        alarms.forEach((a) => {
            const li = document.createElement("li");
            li.className = "alarm-item";
            li.dataset.sev = a.sev;
            li.innerHTML = `
        <span class="alarm-glyph">${glyph[a.sev] || "&#9888;\uFE0F"}</span>
        <span>
          <div class="alarm-title">${a.component}</div>
          <div class="alarm-body">${a.message}</div>
        </span>
        <span class="alarm-code">${a.code}</span>
      `;
            list.appendChild(li);
        });
    }

    const hasIce = alarms.some((a) => a.component === "WIND_TURBINE_1");
    document.getElementById("iceStatus").textContent = hasIce ? "AUTO-HEATER ACTIVE" : "STANDBY";
    document.getElementById("serviceHours").textContent = `${state.serviceHoursRemaining.toFixed(1)} hrs`;
}

/* ---------- Dispatch chart (hand-drawn stacked-area SVG) ---------- */
function renderDispatchChart(dispatch) {
    document.getElementById("dispatchFuel").textContent = `${dispatch.totalFuelL.toFixed(1)} L`;
    document.getElementById("dispatchEmissions").textContent = `${dispatch.totalCo2Kg.toFixed(1)} kg CO\u2082`;
    document.getElementById("dispatchCost").textContent = `$${dispatch.totalCost.toFixed(2)}`;

    const w = 900, h = 260, padL = 36, padR = 10, padT = 10, padB = 22;
    const innerW = w - padL - padR, innerH = h - padT - padB;
    const maxY = 140;
    const x = (hh) => padL + (hh / 24) * innerW;
    const y = (v) => padT + innerH - (v / maxY) * innerH;

    const layers = ["solarKw", "windKw", "battAssistKw", "dieselKw"];
    const colors = { solarKw: "#0D9C94", windKw: "#7C6FE0", battAssistKw: "#1FA971", dieselKw: "#D98A17" };
    const pts = dispatch.points;
    let running = pts.map(() => 0);
    let areas = "";

    layers.forEach((key) => {
        const top = pts.map((p, i) => running[i] + p[key]);
        const topPath = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${x(p.h)} ${y(top[i])}`).join(" ");
        const bottomPath = pts.map((p, i) => `L ${x(pts[pts.length - 1 - i].h)} ${y(running[pts.length - 1 - i])}`).join(" ");
        areas += `<path d="${topPath} ${bottomPath} Z" fill="${colors[key]}" fill-opacity="0.75"/>`;
        running = top;
    });

    const gridLines = [0, 35, 70, 105, 140].map((v) =>
        `<line x1="${padL}" y1="${y(v)}" x2="${w - padR}" y2="${y(v)}" stroke="#E4E9F0" stroke-width="1"/>
     <text x="${padL - 8}" y="${y(v) + 3}" text-anchor="end" font-size="10" fill="#8D97A4">${v}</text>`
    ).join("");
    const hourTicks = [0, 6, 12, 18, 24].map((hh) =>
        `<text x="${x(hh)}" y="${h - 6}" text-anchor="middle" font-size="10" fill="#8D97A4">${hh}h</text>`
    ).join("");

    document.getElementById("dispatchChart").innerHTML = `
    <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid meet">
      ${gridLines}
      ${areas}
      ${hourTicks}
    </svg>
  `;
}

/* ---------- Tabs ---------- */
const TAB_SECTION = { dashboard: "flow", twin: "flow", dispatch: "dispatch", diagnostics: "diagnostics" };
function switchTab(tabKey) {
    document.querySelectorAll(".tab-btn").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === tabKey)));
    const section = TAB_SECTION[tabKey];
    document.getElementById("panel-flow").hidden = section !== "flow";
    document.getElementById("panel-dispatch").hidden = section !== "dispatch";
    document.getElementById("panel-diagnostics").hidden = section !== "diagnostics";
    if (section === "dispatch") renderDispatchChart(buildDispatch(state.scenario));
}

/* ===========================================================
   Main loop
=========================================================== */
let lastTickAt = Date.now();

function tick() {
    const now = Date.now();
    const realSecondsElapsed = (now - lastTickAt) / 1000;
    lastTickAt = now;
    const simHoursElapsed = (realSecondsElapsed * state.speedMultiplier) / 3600;
    state.simTime = new Date(state.simTime.getTime() + realSecondsElapsed * state.speedMultiplier * 1000);

    const sensors = readSensors();
    const derived = stepPower(sensors, simHoursElapsed);
    const alarms = buildAlarms(sensors, derived);

    renderTopbar(sensors);
    renderStatRow(sensors, derived);
    renderFlowMap(sensors, derived);
    renderTwinControls();
    renderAlarms(alarms);

    const activeTab = document.querySelector('.tab-btn[aria-selected="true"]').dataset.tab;
    if (TAB_SECTION[activeTab] === "dispatch") renderDispatchChart(buildDispatch(state.scenario));
}

function restartTimer() {
    if (state.timer) clearInterval(state.timer);
    if (!state.paused) {
        const intervalMs = clamp(4000 / state.speedMultiplier, 400, 4000);
        state.timer = setInterval(tick, intervalMs);
    }
}

/* ---------- Wire up controls ---------- */
function initScenarioSelect() {
    const select = document.getElementById("scenarioSelect");
    SCENARIOS.forEach((sc) => {
        const opt = document.createElement("option");
        opt.value = sc.id;
        opt.textContent = sc.label;
        select.appendChild(opt);
    });
    select.value = state.scenario.id;
    select.addEventListener("change", () => {
        state.scenario = SCENARIOS.find((s) => s.id === select.value);
        lastTickAt = Date.now();
        tick();
    });
}

function initTabs() {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });
}

function initTwinControls() {
    document.getElementById("btnPause").addEventListener("click", () => {
        state.paused = !state.paused;
        lastTickAt = Date.now();
        restartTimer();
        renderTwinControls();
    });

    document.getElementById("btnStep").addEventListener("click", () => {
        state.simTime = new Date(state.simTime.getTime() + 60000);
        const sensors = readSensors();
        const derived = stepPower(sensors, 60 / 3600);
        renderTopbar(sensors);
        renderStatRow(sensors, derived);
        renderFlowMap(sensors, derived);
        renderAlarms(buildAlarms(sensors, derived));
    });

    document.getElementById("btnReset").addEventListener("click", () => {
        Object.assign(state, {
            scenario: SCENARIOS[0], simTime: new Date("2026-09-01T21:43:06Z"),
            speedMultiplier: 1, paused: false, batterySoc: 82.5, fuelLiters: 14200,
            gensetOnline: true, manualLoad: 125.5, serviceHoursRemaining: 579.5, co2CumulativeTonnes: 12.4,
        });
        document.getElementById("scenarioSelect").value = state.scenario.id;
        renderSpeedButtons();
        lastTickAt = Date.now();
        restartTimer();
        tick();
    });

    document.getElementById("gensetToggle").addEventListener("click", () => {
        state.gensetOnline = !state.gensetOnline;
        tick();
    });

    const slider = document.getElementById("loadSlider");
    slider.value = state.manualLoad;
    slider.addEventListener("input", () => {
        state.manualLoad = Number(slider.value);
        document.getElementById("loadSliderValue").textContent = `${state.manualLoad.toFixed(1)} kW`;
    });
    slider.addEventListener("change", () => tick());

    document.getElementById("btnSolve").addEventListener("click", () => {
        renderDispatchChart(buildDispatch(state.scenario));
    });
}

function init() {
    initScenarioSelect();
    initTabs();
    initTwinControls();
    renderSpeedButtons();
    switchTab("dashboard");
    tick();
    restartTimer();
}

document.addEventListener("DOMContentLoaded", init);