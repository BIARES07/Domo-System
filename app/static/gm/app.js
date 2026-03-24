document.addEventListener("DOMContentLoaded", () => {
    fetchTraps();
    fetchMetrics();
    setInterval(fetchMetrics, 3000); // Polling trainee metrics every 3 seconds
});

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
        desc: "If the session (timestamp) is older than 1 hour, data is returned as Base64. Forces the client to re-authenticate or decode buffers.",
        severityType: "N/A",
        severityDesc: "Severity ignored."
    },
    "dynamic_hateoas": {
        name: "DYNAMIC HATEOAS (ADVANCED)",
        desc: "URLs in /init change daily (appending date). Breaks hardcoded client URLs, forcing navigation via links.",
        severityType: "N/A",
        severityDesc: "Severity ignored."
    }
};

async function fetchTraps() {
    const res = await fetch('/api/v1/admin/traps');
    const traps = await res.json();
    const container = document.getElementById('traps-container');
    container.innerHTML = '';
    
    const defaultTraps = [
        "json_mutation", "random_failures", "latency", "binary_tle",
        "schema_drift", "inconsistent_paging", "seed_rotation", "dynamic_hateoas"
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
}

async function updateTrap(trapName, isActive) {
    const severity = parseFloat(document.getElementById(`sev-${trapName}`).value);
    try {
        await fetch(`/api/v1/admin/traps/${trapName}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive, severity: severity })
        });
        console.log(`[PROXY] Trap ${trapName} updated. Status: ${isActive}`);
    } catch(e) {
        console.error("Failed to update trap", e);
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
        
        document.getElementById('status-indicator').innerText = "PROXY LINK ACTIVE";
        document.getElementById('status-indicator').className = "status-ok";
    } catch (e) {
        document.getElementById('status-indicator').innerText = "PROXY LINK LOST";
        document.getElementById('status-indicator').className = "status-alert";
    }
}
