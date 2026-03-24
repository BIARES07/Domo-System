document.addEventListener("DOMContentLoaded", () => {
    // Navigation Logic
    const navBtns = document.querySelectorAll('.nav-btn');
    const views = document.querySelectorAll('.view');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));
            
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
            
            // Load data when view is opened
            if (targetId === 'weather') fetchWeather();
            if (targetId === 'neos') fetchNeos();
            if (targetId === 'satellites') fetchSatellites();
            if (targetId === 'apod') fetchApod();
        });
    });

    // Handshake Logic
    const handshakeBtn = document.getElementById('init-handshake-btn');
    handshakeBtn.addEventListener('click', performHandshake);
});

let cryptoSeed = "";
let sessionActive = false;

function logStatus(msg, isError=false) {
    const log = document.getElementById('handshake-log');
    const span = document.createElement('span');
    span.innerText = `> ${msg}\n`;
    if (isError) span.classList.add('error-text');
    log.appendChild(span);
}

async function performHandshake() {
    logStatus("Initiating link to /api/v1/init...");
    try {
        const res = await fetch('/api/v1/init');
        const data = await res.json();
        
        cryptoSeed = data.crypto_seed;
        sessionActive = true;
        
        logStatus(`Link established. Session ID: ${data.session_id}`);
        logStatus(`Seed received. Applying SHA256 crypto wrapper for future requests...`);
        
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
        'X-Domo-Token': hash
    };
}

async function fetchWeather() {
    if (!sessionActive) {
        document.getElementById('weather-grid').innerHTML = '<p class="error-text">ERR: Handshake required.</p>';
        return;
    }
    try {
        const res = await fetch('/api/v1/intern/weather', { headers: getAuthHeaders() });
        const data = await res.json();
        
        const grid = document.getElementById('weather-grid');
        grid.innerHTML = '';
        
        if (Array.isArray(data)) {
            data.forEach(flare => {
                grid.innerHTML += `
                    <div class="data-card">
                        <h3 style="color:var(--text-main); margin-top:0;">${flare.flrID || flare.flrID_cruda || 'Unknown'}</h3>
                        <p><strong>Class:</strong> ${flare.classType || flare.classType_cruda || 'N/A'}</p>
                        <p><strong>Begin Time:</strong> ${flare.beginTime || flare.beginTime_cruda || 'N/A'}</p>
                    </div>
                `;
            });
        } else {
             grid.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        }
    } catch(e) {
        console.error(e);
    }
}

async function fetchNeos() {
    if (!sessionActive) {
        document.getElementById('neos-grid').innerHTML = '<p class="error-text">ERR: Handshake required.</p>';
        return;
    }
    try {
        const res = await fetch('/api/v1/intern/neos', { headers: getAuthHeaders() });
        const data = await res.json();
        
        const grid = document.getElementById('neos-grid');
        grid.innerHTML = '';
        
        const neosData = data.near_earth_objects || data.near_earth_objects_cruda || {};
        const dates = Object.keys(neosData);
        
        if (dates.length > 0) {
            const firstDate = dates[0];
            const neosList = neosData[firstDate];
            neosList.slice(0, 10).forEach(neo => {
                const name = neo.name || neo.name_cruda || 'Unknown';
                const magnitude = neo.absolute_magnitude_h || neo.absolute_magnitude_h_cruda || 0;
                const hazard = neo.is_potentially_hazardous_asteroid || neo.is_potentially_hazardous_asteroid_cruda ? 'YES' : 'NO';
                
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
        console.error(e);
    }
}

async function fetchSatellites() {
    if (!sessionActive) {
        document.getElementById('sat-body').innerHTML = '<tr><td colspan="4" class="error-text">ERR: Handshake required.</td></tr>';
        return;
    }
    try {
        const res = await fetch('/api/v1/intern/satellites', { headers: getAuthHeaders() });
        
        const tbody = document.getElementById('sat-body');
        tbody.innerHTML = '';

        if (res.headers.get('content-type') === 'application/octet-stream') {
             // Handle binary trap
             const buffer = await res.arrayBuffer();
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
            // Handle JSON (Normal or Mutated)
            const data = await res.json();
            if (Array.isArray(data)) {
                data.forEach(sat => {
                    const id = sat.norad_id || sat.norad_id_cruda || 'N/A';
                    const name = sat.name || sat.name_cruda || 'N/A';
                    const inc = sat.inclination || sat.inclination_cruda || 0;
                    const ecc = sat.eccentricity || sat.eccentricity_cruda || 0;

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
        console.error(e);
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
         const res = await fetch('/api/v1/intern/apod', { headers: getAuthHeaders() });
         const data = await res.json();
         
         const title = data.title || data.title_cruda || 'Unknown APOD';
         const explanation = data.explanation || data.explanation_cruda || 'No description available.';
         const url = data.url || data.url_cruda || '';
         const media_type = data.media_type || data.media_type_cruda || 'image';

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
         console.error(e);
         apodBox.innerHTML = '<p class="error-text">ERR: Feed disrupted.</p>';
     }
}
