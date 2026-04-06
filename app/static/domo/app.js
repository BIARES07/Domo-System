document.addEventListener("DOMContentLoaded", () => {
    const navBtns = document.querySelectorAll('.nav-btn');
    const views = document.querySelectorAll('.view');
    const viewLoaders = {
        weather: fetchWeather,
        neos: fetchNeos,
        satellites: fetchSatellites,
        launches: fetchLaunches,
        conjunctions: fetchConjunctions,
        apod: fetchApod,
    };

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));
            
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');

            if (viewLoaders[targetId]) {
                viewLoaders[targetId]();
            }
        });
    });

    const handshakeBtn = document.getElementById('init-handshake-btn');
    handshakeBtn.addEventListener('click', performHandshake);
});

let cryptoSeed = "";
let sessionActive = false;
let discoveredLinks = {};
let sessionId = "";

function logStatus(msg, isError=false) {
    const log = document.getElementById('handshake-log');
    const span = document.createElement('span');
    span.innerText = `> ${msg}\n`;
    if (isError) span.classList.add('error-text');
    log.appendChild(span);
}

async function performHandshake() {
    logStatus("Initiating link to /api/v1/init/...");
    try {
        const res = await fetch('/api/v1/init/');
        const data = await res.json();
        
        cryptoSeed = data.crypto_seed;
        sessionId = data.session_id || "";
        sessionActive = true;
        discoveredLinks = data.links || {};
        
        logStatus(`Link established. Session ID: ${data.session_id}`);
        logStatus(`Seed received. Applying SHA256 crypto wrapper for future requests...`);
        logStatus(`Discovered modules: ${Object.keys(discoveredLinks).filter(key => key !== 'self').join(', ')}`);
        
        document.getElementById('connection-status').innerHTML = '<span class="dot" style="background-color:#10b981;box-shadow:0 0 8px #10b981;"></span> SECURE LINK ACTIVE';
    } catch (e) {
        logStatus("Failed to reach Gateway.", true);
    }
}

function getAuthHeaders() {
    if (!sessionActive) return {};
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const payload = cryptoSeed + timestamp;
    const hash = CryptoJS.SHA256(payload).toString(CryptoJS.enc.Hex);
    return {
        'X-Domo-Time': timestamp,
        'X-Domo-Token': hash,
        ...(sessionId ? { 'X-Domo-Session': sessionId } : {})
    };
}

function getModulePath(key, fallbackPath) {
    return discoveredLinks[key] || fallbackPath;
}

function readField(payload, key, fallback = 'N/A') {
    if (!payload || typeof payload !== 'object') return fallback;
    if (payload[key] !== undefined && payload[key] !== null) return payload[key];
    const mutatedKey = `${key}_cruda`;
    if (payload[mutatedKey] !== undefined && payload[mutatedKey] !== null) return payload[mutatedKey];
    return fallback;
}

function formatUtc(value) {
    if (!value || value === 'N/A') return 'N/A';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

function extractNumericValue(value, fallback = 0) {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') {
        const match = value.match(/-?\d+(?:\.\d+)?/);
        if (match) return Number(match[0]);
    }
    return fallback;
}

function normalizeLaunches(data) {
    const rawLaunches = Array.isArray(data) ? data : readField(data, 'manifest', []);
    if (!Array.isArray(rawLaunches)) return [];

    return rawLaunches.map(launch => {
        const windowPacket = readField(launch, 'window_packet', {});
        const launchVector = String(readField(launch, 'launch_vector', 'UNKNOWN|N/A'));
        const [vectorStatus, vectorCountdown] = launchVector.includes('|')
            ? launchVector.split('|', 2)
            : ['UNKNOWN', launchVector];

        return {
            ...launch,
            status: readField(launch, 'status', vectorStatus),
            countdown: readField(launch, 'countdown', vectorCountdown),
            window_open_utc: readField(launch, 'window_open_utc', readField(windowPacket, 'open')),
            window_close_utc: readField(launch, 'window_close_utc', readField(windowPacket, 'close')),
        };
    });
}

function normalizeConjunctions(data) {
    const rawAlerts = Array.isArray(data) ? data : readField(data, 'alerts', []);
    if (!Array.isArray(rawAlerts)) return [];

    return rawAlerts.map(alert => {
        const geometry = readField(alert, 'geometry', {});
        const riskScore = readField(alert, 'risk_score', extractNumericValue(readField(alert, 'threat_band', '0'), 0));

        return {
            ...alert,
            risk_score: extractNumericValue(riskScore, 0),
            miss_distance_km: readField(alert, 'miss_distance_km', readField(geometry, 'miss_km', 'N/A')),
            relative_velocity_kms: readField(alert, 'relative_velocity_kms', readField(geometry, 'rel_vel_kms', 'N/A')),
        };
    }).sort((left, right) => extractNumericValue(right.risk_score, 0) - extractNumericValue(left.risk_score, 0));
}

async function fetchProxyPayload(moduleKey, fallbackPath, extraHeaders = {}) {
    const response = await fetch(getModulePath(moduleKey, fallbackPath), {
        headers: {
            ...getAuthHeaders(),
            ...extraHeaders,
        }
    });

    if (!response.ok) {
        let message = `HTTP ${response.status}`;
        try {
            const payload = await response.json();
            message = payload.detail || message;
        } catch (e) {
            // Ignore secondary parsing errors.
        }
        throw new Error(message);
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/octet-stream')) {
        return { __binary: await response.arrayBuffer() };
    }

    const payload = await response.json();
    if (payload && payload.status === 'SESSION_ENCRYPTED_UPGRADE_REQUIRED' && payload.payload_buffer) {
        try {
            return JSON.parse(atob(payload.payload_buffer));
        } catch (e) {
            return payload;
        }
    }

    return payload;
}

async function fetchWeather() {
    if (!sessionActive) {
        document.getElementById('weather-grid').innerHTML = '<p class="error-text">ERR: Handshake required.</p>';
        return;
    }
    try {
        const data = await fetchProxyPayload('weather', '/api/v1/intern/weather');
        
        const grid = document.getElementById('weather-grid');
        grid.innerHTML = '';
        
        if (Array.isArray(data)) {
            data.forEach(flare => {
                grid.innerHTML += `
                    <div class="data-card">
                        <h3 style="color:var(--text-main); margin-top:0;">${readField(flare, 'flrID', 'Unknown')}</h3>
                        <p><strong>Class:</strong> ${readField(flare, 'classType')}</p>
                        <p><strong>Begin Time:</strong> ${readField(flare, 'beginTime')}</p>
                    </div>
                `;
            });
        } else {
             grid.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        }
    } catch(e) {
        document.getElementById('weather-grid').innerHTML = `<p class="error-text">ERR: ${e.message}</p>`;
    }
}

async function fetchNeos() {
    if (!sessionActive) {
        document.getElementById('neos-grid').innerHTML = '<p class="error-text">ERR: Handshake required.</p>';
        return;
    }
    try {
        const data = await fetchProxyPayload('neos', '/api/v1/intern/neos');
        
        const grid = document.getElementById('neos-grid');
        grid.innerHTML = '';
        
        const neosData = readField(data, 'near_earth_objects', {});
        const dates = Object.keys(neosData);
        
        if (dates.length > 0) {
            const firstDate = dates[0];
            const neosList = neosData[firstDate];
            neosList.slice(0, 10).forEach(neo => {
                const name = readField(neo, 'name', 'Unknown');
                const magnitude = readField(neo, 'absolute_magnitude_h', 0);
                const hazard = readField(neo, 'is_potentially_hazardous_asteroid', false) ? 'YES' : 'NO';
                
                grid.innerHTML += `
                    <div class="data-card" style="border-color: ${hazard === 'YES' ? '#ef4444' : 'var(--border-dim)'}">
                        <h3 style="color:var(--text-main); margin-top:0;">${name}</h3>
                        <p><strong>Magnitude (H):</strong> ${magnitude}</p>
                        <p><strong>Hazardous:</strong> <span style="color:${hazard==='YES'?'#ef4444':'#10b981'}">${hazard}</span></p>
                    </div>
                `;
            });
        }
    } catch(e) {
        document.getElementById('neos-grid').innerHTML = `<p class="error-text">ERR: ${e.message}</p>`;
    }
}

async function fetchSatellites() {
    if (!sessionActive) {
        document.getElementById('sat-body').innerHTML = '<tr><td colspan="4" class="error-text">ERR: Handshake required.</td></tr>';
        return;
    }
    try {
        const tbody = document.getElementById('sat-body');
        tbody.innerHTML = '';

           const data = await fetchProxyPayload('satellites', '/api/v1/intern/satellites', { 'X-Domo-Range': 'items=0-9' });

           if (data.__binary) {
               const buffer = data.__binary;
             const view = new DataView(buffer);
             
             let offset = 0;
             while (offset < buffer.byteLength) {
                 const noradId = view.getUint32(offset, true); // Little endian
                 offset += 4;
                 const lat = view.getFloat32(offset, true); offset += 4;
                 const lon = view.getFloat32(offset, true); offset += 4;
                 const alt = view.getFloat32(offset, true); offset += 4;
                 const vel = view.getFloat32(offset, true); offset += 4;

                 tbody.innerHTML += `
                    <tr style="color: #fbbf24;">
                        <td>${noradId} <span style="font-size:10px;">[BIN_DECODE]</span></td>
                        <td>UNKNOWN_BIN_PAYLOAD</td>
                        <td>${lat.toFixed(4)}</td>
                        <td>${vel.toFixed(4)}</td>
                    </tr>
                `;
             }
        } else {
            const rows = Array.isArray(data) ? data : readField(data, 'items', []);
            if (Array.isArray(rows)) {
                rows.forEach(sat => {
                    const id = readField(sat, 'norad_id');
                    const name = readField(sat, 'name');
                    const inc = readField(sat, 'inclination', 0);
                    const ecc = readField(sat, 'eccentricity', 0);

                    tbody.innerHTML += `
                        <tr>
                            <td>${id}</td>
                            <td>${name}</td>
                            <td>${inc}</td>
                            <td>${ecc}</td>
                        </tr>
                    `;
                });
            } else {
                tbody.innerHTML = `<tr><td colspan="4"><pre>${JSON.stringify(data, null, 2)}</pre></td></tr>`;
            }
        }
    } catch(e) {
        document.getElementById('sat-body').innerHTML = `<tr><td colspan="4" class="error-text">ERR: ${e.message}</td></tr>`;
    }
}

async function fetchLaunches() {
    const grid = document.getElementById('launches-grid');
    if (!sessionActive) {
        grid.innerHTML = '<p class="error-text">ERR: Handshake required.</p>';
        return;
    }

    grid.innerHTML = '<p>Synchronizing mission queue...</p>';
    try {
        const data = await fetchProxyPayload('launches', '/api/v1/intern/launches');
        const launches = normalizeLaunches(data);
        if (!Array.isArray(launches) || launches.length === 0) {
            grid.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            return;
        }

        grid.innerHTML = launches.map(launch => {
            const status = readField(launch, 'status');
            const readiness = readField(launch, 'readiness');
            return `
                <article class="data-card">
                    <div class="status-badge">${status} / ${readiness}</div>
                    <h3 style="color:var(--text-main); margin-top:0;">${readField(launch, 'mission_name')}</h3>
                    <p class="module-note">${readField(launch, 'mission_brief')}</p>
                    <div class="metric-strip">
                        <div class="metric-chip"><strong>COUNTDOWN</strong>${readField(launch, 'countdown')}</div>
                        <div class="metric-chip"><strong>ORBIT</strong>${readField(launch, 'orbit_class')}</div>
                        <div class="metric-chip"><strong>VEHICLE</strong>${readField(launch, 'vehicle')}</div>
                    </div>
                    <div class="launch-meta">
                        <div><strong>Provider:</strong> ${readField(launch, 'provider')}</div>
                        <div><strong>Site:</strong> ${readField(launch, 'launch_site')}</div>
                        <div><strong>Payload:</strong> ${readField(launch, 'payload')}</div>
                        <div><strong>Window:</strong> ${formatUtc(readField(launch, 'window_open_utc'))} - ${formatUtc(readField(launch, 'window_close_utc'))}</div>
                    </div>
                </article>
            `;
        }).join('');
    } catch (e) {
        grid.innerHTML = `<p class="error-text">ERR: ${e.message}</p>`;
    }
}

async function fetchConjunctions() {
    const grid = document.getElementById('conjunctions-grid');
    if (!sessionActive) {
        grid.innerHTML = '<p class="error-text">ERR: Handshake required.</p>';
        return;
    }

    grid.innerHTML = '<p>Interpolating orbital conflict geometry...</p>';
    try {
        const data = await fetchProxyPayload('conjunctions', '/api/v1/intern/conjunctions');
        const alerts = normalizeConjunctions(data);
        if (!Array.isArray(alerts) || alerts.length === 0) {
            grid.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            return;
        }

        grid.innerHTML = alerts.map(alert => {
            const level = String(readField(alert, 'alert_level', 'MONITOR')).toLowerCase();
            return `
                <article class="data-card">
                    <div class="risk-badge risk-${level}">${readField(alert, 'alert_level')}</div>
                    <h3 style="color:var(--text-main); margin-top:0;">${readField(alert, 'primary_name')} vs ${readField(alert, 'secondary_name')}</h3>
                    <div class="metric-strip">
                        <div class="metric-chip"><strong>RISK</strong>${readField(alert, 'risk_score')}</div>
                        <div class="metric-chip"><strong>MISS DIST</strong>${readField(alert, 'miss_distance_km')} km</div>
                        <div class="metric-chip"><strong>REL VEL</strong>${readField(alert, 'relative_velocity_kms')} km/s</div>
                    </div>
                    <div class="conjunction-meta">
                        <div><strong>TCA:</strong> ${formatUtc(readField(alert, 'tca_utc'))}</div>
                        <div><strong>Primary NORAD:</strong> ${readField(alert, 'primary_norad_id')}</div>
                        <div><strong>Secondary NORAD:</strong> ${readField(alert, 'secondary_norad_id')}</div>
                        <div><strong>Action:</strong> ${readField(alert, 'recommended_action')}</div>
                    </div>
                </article>
            `;
        }).join('');
    } catch (e) {
        grid.innerHTML = `<p class="error-text">ERR: ${e.message}</p>`;
    }
}

async function fetchApod() {
    if (!sessionActive) {
        document.getElementById('apod-content').innerHTML = '<p class="error-text">ERR: Handshake required.</p>';
        return;
    }
     const apodBox = document.getElementById('apod-content');
     apodBox.innerHTML = '<p>Loading uplink...</p>';
     try {
         const data = await fetchProxyPayload('apod', '/api/v1/intern/apod');
         
         const title = readField(data, 'title', 'Unknown APOD');
         const explanation = readField(data, 'explanation', 'No description available.');
         const url = readField(data, 'url', '');
         const media_type = readField(data, 'media_type', 'image');

         if (media_type === 'video') {
              apodBox.innerHTML = `
                <iframe src="${url}" frameborder="0" allowfullscreen style="width:100%; height:400px; border:1px solid var(--border-dim); border-radius:8px; margin-bottom:20px;"></iframe>
                <p><strong>Title:</strong> ${title}</p>
                <p>${explanation}</p>
             `;
         } else {
             apodBox.innerHTML = `
                <img src="${url}" alt="${title}">
                <p><strong>Title:</strong> ${title}</p>
                <p>${explanation}</p>
             `;
         }
     } catch (e) {
         apodBox.innerHTML = `<p class="error-text">ERR: ${e.message}</p>`;
     }
}
