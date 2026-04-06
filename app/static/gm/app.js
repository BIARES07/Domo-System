document.addEventListener("DOMContentLoaded", () => {
    fetchTraps();
    fetchDashboardData();
    fetchMetrics();
    setInterval(fetchDashboardData, 10000);
    setInterval(fetchMetrics, 3000); // Polling trainee metrics every 3 seconds
});

let latestTraps = [];
let dashboardSnapshot = null;
const linkHealth = {
    traps: false,
    dashboard: false,
    metrics: false,
};

const trapDescriptions = {
    "json_mutation": {
        name: "JSON MUTATION (NIVEL 1)",
        desc: "Recursively alters JSON keys by appending '_cruda' to them. Breaks frontend parsers that expect strict schemas.",
        severityType: "N/A",
        severityDesc: "Severity ignored. Toggle is binary."
    },
    "random_failures": {
        name: "HTTP CHAOS (NIVEL 2)",
        desc: "Injects random HTTP errors (500 Internal Server Error, 429 Too Many Requests, 503 Service Unavailable).",
        severityType: "Probability",
        severityDesc: "Value represents the % of requests that will fail (0.0 = 0%, 1.0 = 100%)."
    },
    "latency": {
        name: "NETWORK LATENCY (NIVEL 2)",
        desc: "Forces a random delay between 1 to 5 seconds before returning a response, causing timeouts.",
        severityType: "Probability",
        severityDesc: "Value represents the % of requests that will be delayed (0.0 = 0%, 1.0 = 100%)."
    },
    "binary_tle": {
        name: "BINARY PAYLOAD (NIVEL 3)",
        desc: "Overrides the /satellites endpoint. Instead of JSON, returns an 'application/octet-stream' packed with C-struct binary (Little-Endian floats).",
        severityType: "N/A",
        severityDesc: "Severity ignored. Toggle is binary."
    },
    "schema_drift": {
        name: "SCHEMA DRIFT (ADVANCED)",
        desc: "Changes numeric values to strings with units (e.g., 100 -> '100 km/s'). Breaks strict type-casting and arithmetic in clients.",
        severityType: "N/A",
        severityDesc: "Severity ignored."
    },
    "inconsistent_paging": {
        name: "INCONSISTENT PAGING (ADVANCED)",
        desc: "Forces pagination on /satellites. Requires 'X-Domo-Range' header (e.g., items=0-2) to fetch more than 3 items.",
        severityType: "N/A",
        severityDesc: "Severity ignored."
    },
    "seed_rotation": {
        name: "SEED ROTATION (ADVANCED)",
        desc: "If the authenticated session is older than 1 hour, data is returned as Base64. Fresh timestamps still pass auth, but stale sessions trigger re-authentication logic.",
        severityType: "N/A",
        severityDesc: "Severity ignored."
    },
    "dynamic_hateoas": {
        name: "DYNAMIC HATEOAS (ADVANCED)",
        desc: "URLs in /init change daily (appending date). Breaks hardcoded client URLs, forcing navigation via links.",
        severityType: "N/A",
        severityDesc: "Severity ignored."
    },
    "launch_window_fragmentation": {
        name: "LAUNCH WINDOW FRAGMENTATION",
        desc: "Reshapes /launches into a manifest packet with nested window data and a combined launch vector string.",
        severityType: "N/A",
        severityDesc: "Severity ignored. Toggle is binary."
    },
    "conjunction_signal_scramble": {
        name: "CONJUNCTION SIGNAL SCRAMBLE",
        desc: "Wraps /conjunctions in a packet, reorders alerts chronologically and encodes risk as a threat band plus nested geometry.",
        severityType: "N/A",
        severityDesc: "Severity ignored. Toggle is binary."
    }
};

async function fetchTraps() {
    try {
        const res = await fetch('/api/v1/admin/traps');
        if (!res.ok) throw new Error('Failed to fetch traps');

        const traps = await res.json();
        latestTraps = traps;

        const container = document.getElementById('traps-container');
        container.innerHTML = '';
        
        const defaultTraps = [
            "json_mutation", "random_failures", "latency", "binary_tle",
            "schema_drift", "inconsistent_paging", "seed_rotation", "dynamic_hateoas",
            "launch_window_fragmentation", "conjunction_signal_scramble"
        ];
        
        defaultTraps.forEach(trapName => {
            const trap = traps.find(t => t.trap_name === trapName) || { trap_name: trapName, is_active: false, severity: 0.0 };
            const meta = trapDescriptions[trapName] || { name: trapName.toUpperCase(), desc: "Unknown trap.", severityType: "Value", severityDesc: "" };
            
            const card = document.createElement('div');
            card.className = 'trap-card';
            card.innerHTML = `
                <div class="trap-header">
                    <div class="trap-title">${meta.name}</div>
                    <div class="trap-controls">
                        <label style="font-size:12px; color:var(--text-secondary);">
                            SEVERITY: <input type="number" step="0.1" min="0" max="1" value="${trap.severity}" id="sev-${trap.trap_name}" style="width: 50px; background:var(--bg-dark); color:var(--text-primary); border:1px solid var(--border-color);" ${meta.severityType === 'N/A' ? 'disabled' : ''}>
                        </label>
                        <label class="toggle-switch">
                            <input type="checkbox" ${trap.is_active ? 'checked' : ''} onchange="updateTrap('${trap.trap_name}', this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>
                <div class="trap-desc">${meta.desc}</div>
                <div style="font-size:11px; color:#555;">// SEVERITY: ${meta.severityDesc}</div>
            `;
            container.appendChild(card);
        });

        renderSummary();
        updateLinkHealth('traps', true);
    } catch (e) {
        updateLinkHealth('traps', false);
    }
}

async function updateTrap(trapName, isActive) {
    const severity = parseFloat(document.getElementById(`sev-${trapName}`).value);
    try {
        await fetch(`/api/v1/admin/traps/${trapName}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive, severity: severity })
        });
        fetchTraps();
    } catch(e) {
        console.error("Failed to update trap", e);
    }
}

async function fetchDashboardData() {
    try {
        const res = await fetch('/api/v1/admin/dashboard/data');
        if (!res.ok) throw new Error('Failed to fetch dashboard data');

        dashboardSnapshot = await res.json();
        renderSummary();
        renderLaunches(dashboardSnapshot.launches || []);
        renderConjunctions(dashboardSnapshot.conjunctions || []);
        updateLinkHealth('dashboard', true);
    } catch (e) {
        renderLaunches([]);
        renderConjunctions([]);
        updateLinkHealth('dashboard', false);
    }
}

async function fetchMetrics() {
    try {
        const res = await fetch('/api/v1/admin/metrics');
        if (!res.ok) throw new Error("Failed to fetch metrics");
        
        const metrics = await res.json();
        const tbody = document.getElementById('metrics-body');
        tbody.innerHTML = '';
        
        metrics.forEach(m => {
            const date = new Date(m.timestamp).toLocaleTimeString();
            let statusClass = "status-200";
            if (m.status_code >= 400 && m.status_code < 500) statusClass = "status-429";
            if (m.status_code >= 500 || m.status_code === 401) statusClass = "status-500";
            
            tbody.innerHTML += `
                <tr>
                    <td>${date}</td>
                    <td style="color:var(--text-secondary);">${m.endpoint_accessed}</td>
                    <td><span class="status-code ${statusClass}">${m.status_code}</span></td>
                    <td>${m.response_time_ms.toFixed(2)}</td>
                    <td style="color:#555;">${m.client_ip}</td>
                </tr>
            `;
        });

        updateLinkHealth('metrics', true);
    } catch (e) {
        updateLinkHealth('metrics', false);
    }
}

function renderSummary() {
    const summary = document.getElementById('intel-summary');
    if (!summary) return;

    const launches = Array.isArray(dashboardSnapshot?.launches) ? dashboardSnapshot.launches : [];
    const conjunctions = Array.isArray(dashboardSnapshot?.conjunctions) ? dashboardSnapshot.conjunctions : [];
    const satellites = Array.isArray(dashboardSnapshot?.satellites) ? dashboardSnapshot.satellites : [];
    const weather = Array.isArray(dashboardSnapshot?.weather) ? dashboardSnapshot.weather : [];
    const activeTrapCount = latestTraps.filter(trap => trap.is_active).length;
    const highRiskCount = conjunctions.filter(item => (item.risk_score || 0) >= 65).length;

    summary.innerHTML = `
        <article class="summary-card">
            <div class="summary-label">ACTIVE TRAPS</div>
            <div class="summary-value">${activeTrapCount}</div>
            <div class="summary-detail">Proxy hostility profiles currently armed.</div>
        </article>
        <article class="summary-card">
            <div class="summary-label">UPCOMING LAUNCHES</div>
            <div class="summary-value">${launches.length}</div>
            <div class="summary-detail">Mission windows queued in operator feed.</div>
        </article>
        <article class="summary-card">
            <div class="summary-label">HIGH-RISK CONJUNCTIONS</div>
            <div class="summary-value">${highRiskCount}</div>
            <div class="summary-detail">Events with HIGH or CRITICAL posture.</div>
        </article>
        <article class="summary-card">
            <div class="summary-label">TRACKED ASSETS</div>
            <div class="summary-value">${satellites.length}</div>
            <div class="summary-detail">Satellites in current admin telemetry snapshot, flares ${weather.length}.</div>
        </article>
    `;
}

function renderLaunches(launches) {
    const container = document.getElementById('launches-list');
    if (!container) return;

    if (!Array.isArray(launches) || launches.length === 0) {
        container.innerHTML = '<div class="empty-state">No launch windows available from the admin feed.</div>';
        return;
    }

    container.innerHTML = launches.slice(0, 4).map(launch => `
        <article class="intel-item">
            <div class="intel-badge">${launch.status} / ${launch.readiness}</div>
            <h4>${launch.mission_name}</h4>
            <div class="item-grid">
                <div class="item-chip"><strong>COUNTDOWN</strong>${launch.countdown}</div>
                <div class="item-chip"><strong>ORBIT</strong>${launch.orbit_class}</div>
                <div class="item-chip"><strong>VEHICLE</strong>${launch.vehicle}</div>
                <div class="item-chip"><strong>SITE</strong>${launch.launch_site}</div>
            </div>
            <div class="item-note">${launch.mission_brief}</div>
        </article>
    `).join('');
}

function renderConjunctions(conjunctions) {
    const container = document.getElementById('conjunctions-list');
    if (!container) return;

    if (!Array.isArray(conjunctions) || conjunctions.length === 0) {
        container.innerHTML = '<div class="empty-state">No conjunction warnings available from the admin feed.</div>';
        return;
    }

    container.innerHTML = conjunctions.slice(0, 4).map(alert => {
        const levelClass = String(alert.alert_level || 'monitor').toLowerCase();
        return `
            <article class="intel-item">
                <div class="intel-badge ${levelClass}">${alert.alert_level}</div>
                <h4>${alert.primary_name} vs ${alert.secondary_name}</h4>
                <div class="item-grid">
                    <div class="item-chip"><strong>RISK</strong>${alert.risk_score}</div>
                    <div class="item-chip"><strong>MISS DIST</strong>${alert.miss_distance_km} km</div>
                    <div class="item-chip"><strong>REL VEL</strong>${alert.relative_velocity_kms} km/s</div>
                    <div class="item-chip"><strong>TCA</strong>${new Date(alert.tca_utc).toLocaleTimeString()}</div>
                </div>
                <div class="item-note">${alert.recommended_action}</div>
            </article>
        `;
    }).join('');
}

function updateLinkHealth(part, ok) {
    linkHealth[part] = ok;
    const isHealthy = Object.values(linkHealth).every(Boolean);
    const status = document.getElementById('status-indicator');
    status.innerText = isHealthy ? 'PROXY LINK ACTIVE' : 'PROXY LINK DEGRADED';
    status.className = isHealthy ? 'status-ok' : 'status-alert';

    if (ok) {
        document.getElementById('last-refresh').innerText = `LAST SYNC ${new Date().toLocaleTimeString()}`;
    }
}
