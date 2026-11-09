/**
 * app.js - Cliente WebSocket y Lógica del Monitor SOC 1080p.
 * "El Rayos X del Wi-Fi Público: Lo que tu celular dice a tus espaldas"
 */

document.addEventListener("DOMContentLoaded", () => {
    let ws = null;
    let serverIp = "127.0.0.1";
    let serverPort = 8000;
    let activeQrUrl = "";
    let hallwayActive = true;
    let isMuted = false;
    let knownNodes = new Set();

    // Referencias al DOM
    const wsStatus = document.getElementById("wsStatus");
    const metricVisitors = document.getElementById("metricVisitors");
    const metricPlain = document.getElementById("metricPlain");
    const metricEncrypted = document.getElementById("metricEncrypted");
    const clockDisplay = document.getElementById("clockDisplay");
    
    const devicesList = document.getElementById("devicesList");
    const nodesCountBadge = document.getElementById("nodesCountBadge");
    const radarBlips = document.getElementById("radarBlips");
    
    const telemetryStream = document.getElementById("telemetryStream");
    const telemetryStateBadge = document.getElementById("telemetryStateBadge");
    
    const inspectorEmpty = document.getElementById("inspectorEmpty");
    const inspectorCard = document.getElementById("inspectorCard");
    const inspectStatus = document.getElementById("inspectStatus");
    const inspectNode = document.getElementById("inspectNode");
    const inspectTime = document.getElementById("inspectTime");
    const inspectAlias = document.getElementById("inspectAlias");
    const inspectPayloadContent = document.getElementById("inspectPayloadContent");
    const inspectSha = document.getElementById("inspectSha");
    const mitmTotalBadge = document.getElementById("mitmTotalBadge");
    const protectedWallList = document.getElementById("protectedWallList");

    const fullScreenAlert = document.getElementById("fullScreenAlert");
    const alertNode = document.getElementById("alertNode");
    const alertAlias = document.getElementById("alertAlias");
    const alertPayload = document.getElementById("alertPayload");

    const qrModal = document.getElementById("qrModal");
    const btnZoomQr = document.getElementById("btnZoomQr");
    const btnCloseModal = document.getElementById("btnCloseModal");
    const modalUrlDisplay = document.getElementById("modalUrlDisplay");
    const modalIpSelect = document.getElementById("modalIpSelect");
    const topIpLabel = document.getElementById("topIpLabel");
    const bannerUrlText = document.getElementById("bannerUrlText");

    // Botones de Expositor
    const btnDemoVisitor = document.getElementById("btnDemoVisitor");
    const btnDemoMitm = document.getElementById("btnDemoMitm");
    const btnToggleHallway = document.getElementById("btnToggleHallway");
    const btnToggleAudio = document.getElementById("btnToggleAudio");
    const btnFullscreen = document.getElementById("btnFullscreen");
    const btnResetRoom = document.getElementById("btnResetRoom");

    // 1. Reloj en tiempo real
    function startClock() {
        setInterval(() => {
            const now = new Date();
            clockDisplay.textContent = now.toTimeString().split(" ")[0];
        }, 1000);
    }

    // 2. Cargar información de red y configurar el Código QR
    async function initNetworkInfo() {
        try {
            const res = await fetch("/api/network-info");
            if (res.ok) {
                const data = await res.json();
                serverIp = data.server_ip;
                serverPort = data.port || 8000;
                
                // Poblar selector de interfaces si hay más de una
                modalIpSelect.innerHTML = "";
                data.available_ips.forEach(ip => {
                    const opt = document.createElement("option");
                    opt.value = ip;
                    opt.textContent = `${ip} (Puerto ${serverPort})`;
                    if (ip === serverIp) opt.selected = true;
                    modalIpSelect.appendChild(opt);
                });

                updateQrCodes(serverIp);
            }
        } catch (err) {
            console.warn("Fallo al obtener network-info, usando IP actual:", err);
            updateQrCodes(window.location.hostname || "127.0.0.1");
        }
    }

    function updateQrCodes(selectedIp) {
        serverIp = selectedIp;
        activeQrUrl = `http://${serverIp}:${serverPort}/reto`;
        topIpLabel.textContent = activeQrUrl;
        bannerUrlText.textContent = activeQrUrl;
        modalUrlDisplay.textContent = activeQrUrl;

        // Renderizar QR en el modal
        if (window.QRCode) {
            new QRCode("modalQrContainer", {
                text: activeQrUrl,
                width: 280,
                height: 280,
                colorDark: "#000000",
                colorLight: "#ffffff"
            });
        }
    }

    modalIpSelect.addEventListener("change", (e) => {
        updateQrCodes(e.target.value);
    });

    // 3. Conexión WebSocket
    function connectWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            wsStatus.className = "status-pill status-live";
            wsStatus.textContent = "● EN VIVO";
        };

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                handleWsMessage(msg);
            } catch (e) {
                console.error("Error parseando mensaje WS:", e);
            }
        };

        ws.onclose = () => {
            wsStatus.className = "status-pill status-down";
            wsStatus.textContent = "○ RECONECTANDO...";
            setTimeout(connectWebSocket, 2000);
        };

        ws.onerror = () => {
            ws.close();
        };
    }

    // 4. Despachador de Mensajes WS
    function handleWsMessage(msg) {
        switch (msg.type) {
            case "initial_state":
                loadInitialState(msg);
                break;
            case "node_joined":
                handleNodeJoined(msg);
                break;
            case "telemetry_tick":
                handleTelemetryTick(msg.tick);
                break;
            case "mitm_event":
                handleMitmEvent(msg);
                break;
            case "simulation_state":
                hallwayActive = msg.simulation_active;
                btnToggleHallway.textContent = `Pasillo: ${hallwayActive ? 'ACTIVO' : 'PAUSADO'} [P]`;
                telemetryStateBadge.textContent = hallwayActive ? "RASTREO EN VIVO" : "RASTREO PAUSADO";
                break;
            case "room_reset":
                resetDashboardUI();
                break;
        }
    }

    // Carga de Estado Inicial
    function loadInitialState(data) {
        if (data.metrics) updateMetrics(data.metrics);
        if (data.devices) {
            devicesList.innerHTML = "";
            radarBlips.innerHTML = "";
            knownNodes.clear();
            data.devices.forEach(dev => renderDevice(dev, false));
        }
        if (data.protected_wall) {
            renderProtectedWall(data.protected_wall);
        }
        if (data.events && data.events.length > 0) {
            renderMitmInspector(data.events[0]);
        }
        hallwayActive = !!data.simulation_active;
        btnToggleHallway.textContent = `Pasillo: ${hallwayActive ? 'ACTIVO' : 'PAUSADO'} [P]`;
    }

    // Actualizar Contadores Métricos
    function updateMetrics(metrics) {
        metricVisitors.textContent = String(metrics.total_visitors || 0).padStart(2, "0");
        metricPlain.textContent = String(metrics.plain_captures || 0).padStart(2, "0");
        metricEncrypted.textContent = String(metrics.encrypted_blocks || 0).padStart(2, "0");
        
        const totalMitm = (metrics.plain_captures || 0) + (metrics.encrypted_blocks || 0);
        mitmTotalBadge.textContent = `${totalMitm} PRUEBAS`;
    }

    // Evento: Nuevo Nodo Conectado
    function handleNodeJoined(data) {
        if (window.socAudio) window.socAudio.playSonar();
        if (data.metrics) updateMetrics(data.metrics);
        renderDevice(data.fingerprint, true);
    }

    // Renderizar Tarjeta de Dispositivo y Blip en Radar
    function renderDevice(fp, animate) {
        const nodeId = fp.node_id || "#01";
        if (knownNodes.has(nodeId)) return;
        knownNodes.add(nodeId);

        // Remover placeholder de lista vacía
        const empty = devicesList.querySelector(".empty-state");
        if (empty) empty.remove();

        const card = document.createElement("div");
        card.className = "device-card";
        card.innerHTML = `
            <div class="dev-card-top">
                <span class="dev-node-id">${nodeId}</span>
                <span class="dev-os-badge">${fp.os || 'Dispositivo'}</span>
            </div>
            <div class="dev-details-grid">
                <div><span class="d-k">IP:</span> <span class="d-v">${fp.ip_anonima || '192.168.1.***'}</span></div>
                <div><span class="d-k">Navegador:</span> <span class="d-v">${fp.navegador || 'Web'}</span></div>
                <div><span class="d-k">Pantalla:</span> <span class="d-v">${fp.resolucion || '1080x2400'}</span></div>
                <div><span class="d-k">Gráfica:</span> <span class="d-v">${(fp.gpu || 'Mali / Adreno').substring(0, 16)}</span></div>
            </div>
        `;
        devicesList.prepend(card);
        nodesCountBadge.textContent = `${knownNodes.size} ACTIVOS`;

        addRadarBlip(nodeId);
    }

    function addRadarBlip(nodeId) {
        const blip = document.createElement("div");
        blip.className = "radar-blip";
        blip.id = `blip-${nodeId.replace('#', '')}`;

        const angle = (knownNodes.size * 137.5) * (Math.PI / 180);
        const radius = 22 + ((knownNodes.size * 18) % 55);
        
        const x = 50 + (radius * Math.cos(angle));
        const y = 50 + (radius * Math.sin(angle));

        blip.style.left = `${Math.min(88, Math.max(12, x))}%`;
        blip.style.top = `${Math.min(88, Math.max(12, y))}%`;

        const label = document.createElement("span");
        label.className = "radar-blip-label";
        label.textContent = nodeId;
        blip.appendChild(label);

        radarBlips.appendChild(blip);
    }

    // Evento: Telemetría / Consulta DNS en Cascada
    function handleTelemetryTick(tick) {
        if (!tick) return;
        if (window.socAudio) window.socAudio.playTick();

        const row = document.createElement("div");
        row.className = "stream-row";

        let catClass = "cat-os";
        if (tick.category.includes("SOCIAL")) catClass = "cat-social";
        else if (tick.category.includes("RASTREADOR")) catClass = "cat-tracker";
        else if (tick.category.includes("MENSAJERÍA")) catClass = "cat-msg";

        row.innerHTML = `
            <span class="stream-time">${tick.timestamp}</span>
            <span class="stream-node">${tick.node_id}</span>
            <span class="badge-cat ${catClass}">${tick.category}</span>
            <div class="stream-body">
                <span class="stream-domain">${tick.domain}</span>
                <span class="stream-desc">${tick.description}</span>
            </div>
        `;

        telemetryStream.prepend(row);

        if (telemetryStream.children.length > 70) {
            telemetryStream.removeChild(telemetryStream.lastChild);
        }
    }

    // Evento: Transmisión MitM (Texto Plano vs. Cifrado)
    function handleMitmEvent(ev) {
        if (ev.metrics) updateMetrics(ev.metrics);
        renderMitmInspector(ev);

        const isPlain = (ev.mode === "plain");

        if (isPlain) {
            if (window.socAudio) window.socAudio.playPlainAlert();
            triggerFullScreenAlert(ev);
        } else {
            if (window.socAudio) window.socAudio.playEncryptedShield();
            if (ev.protected_wall) {
                renderProtectedWall(ev.protected_wall);
            }
        }
    }

    function renderMitmInspector(ev) {
        inspectorEmpty.classList.add("hidden");
        inspectorCard.classList.remove("hidden", "mode-plain", "mode-encrypted");

        const isPlain = (ev.mode === "plain");
        inspectorCard.classList.add(isPlain ? "mode-plain" : "mode-encrypted");

        inspectStatus.textContent = isPlain ? "⚠️ INTERCEPTADO EN TEXTO PLANO" : "🛡️ BLINDADO CON CIFRADO (TLS/AES)";
        inspectNode.textContent = ev.node_id || "#01";
        inspectTime.textContent = ev.timestamp || new Date().toTimeString().split(" ")[0];
        inspectAlias.textContent = ev.alias || "visitante";

        if (isPlain) {
            inspectPayloadContent.textContent = ev.payload_preview || `POST /login HTTP/1.1\r\nuser=${ev.alias}&pass=${ev.secret}`;
            inspectSha.textContent = "NINGUNO (DATO TOTALMENTE DESPROTEGIDO)";
        } else {
            inspectPayloadContent.textContent = `[TÚNEL CIFRADO TLS 1.3 / AES-256]\n${ev.cipher_hex || '16 03 03 ...'}`;
            inspectSha.textContent = ev.sha256 || "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
        }
    }

    function triggerFullScreenAlert(ev) {
        alertNode.textContent = `DISPOSITIVO: ${ev.node_id || '#01'}`;
        alertAlias.textContent = `USUARIO: ${ev.alias || 'victima'}`;
        alertPayload.textContent = ev.payload_preview || `POST /api/login HTTP/1.1\r\nuser=${ev.alias}&pass=${ev.secret}`;

        fullScreenAlert.classList.remove("hidden");
        setTimeout(() => {
            fullScreenAlert.classList.add("hidden");
        }, 3600);
    }

    // Renderizar Muro de Usuarios Protegidos
    function renderProtectedWall(wallItems) {
        if (!wallItems || wallItems.length === 0) return;
        protectedWallList.innerHTML = "";

        wallItems.forEach(item => {
            const el = document.createElement("div");
            el.className = "wall-item";
            el.innerHTML = `
                <div>
                    <span class="wall-item-alias">${item.alias}</span>
                    <span class="term-dim">(${item.node_id})</span>
                    <div class="wall-item-hash">SHA: ${item.sha256}</div>
                </div>
                <div class="wall-item-time">${item.timestamp || 'PROTEGIDO'}</div>
            `;
            protectedWallList.appendChild(el);
        });
    }

    // Reinicio Total de la Sala
    function resetDashboardUI() {
        metricVisitors.textContent = "00";
        metricPlain.textContent = "00";
        metricEncrypted.textContent = "00";
        mitmTotalBadge.textContent = "0 PRUEBAS";
        nodesCountBadge.textContent = "0 ACTIVOS";
        
        knownNodes.clear();
        radarBlips.innerHTML = "";
        devicesList.innerHTML = `<div class="empty-state"><span class="cursor-blink">&gt;</span> Esperando dispositivos... Escanea el código QR desde tu celular para ingresar como el <strong>Nodo #01</strong>.</div>`;
        telemetryStream.innerHTML = "";
        protectedWallList.innerHTML = `<div class="empty-state">Aún nadie ha blindado su conexión. Pulsa el botón verde en tu celular para ingresar a esta lista de honor.</div>`;
        
        inspectorCard.classList.add("hidden");
        inspectorEmpty.classList.remove("hidden");
    }

    // 5. Controles del Expositor
    btnDemoVisitor.addEventListener("click", () => fetch("/api/demo/visitor", { method: "POST" }));
    btnDemoMitm.addEventListener("click", () => fetch("/api/demo/mitm", { method: "POST" }));
    
    btnToggleHallway.addEventListener("click", async () => {
        const res = await fetch("/api/demo/hallway", { method: "POST" });
        if (res.ok) {
            const d = await res.json();
            hallwayActive = d.simulation_active;
            btnToggleHallway.textContent = `Pasillo: ${hallwayActive ? 'ACTIVO' : 'PAUSADO'} [P]`;
            telemetryStateBadge.textContent = hallwayActive ? "RASTREO EN VIVO" : "RASTREO PAUSADO";
        }
    });

    btnToggleAudio.addEventListener("click", () => {
        if (window.socAudio) {
            isMuted = window.socAudio.toggleMute();
            btnToggleAudio.textContent = `Sonido: ${isMuted ? 'SILENCIADO' : 'ACTIVO'} [M]`;
            btnToggleAudio.style.color = isMuted ? 'var(--term-red)' : 'var(--term-green)';
        }
    });

    btnFullscreen.addEventListener("click", () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(() => {});
            btnFullscreen.textContent = "Salir Pantalla Completa [F]";
        } else {
            document.exitFullscreen().catch(() => {});
            btnFullscreen.textContent = "Pantalla Completa [F]";
        }
    });

    btnResetRoom.addEventListener("click", () => {
        if (confirm("¿Deseas reiniciar todas las estadísticas y limpiar los dispositivos de la sala?")) {
            fetch("/api/reset", { method: "POST" });
        }
    });

    // Control del Modal de QR
    btnZoomQr.addEventListener("click", () => qrModal.classList.remove("hidden"));
    bannerUrlText.addEventListener("click", () => qrModal.classList.remove("hidden"));
    btnCloseModal.addEventListener("click", () => qrModal.classList.add("hidden"));

    // 6. Atajos de Teclado del Expositor
    window.addEventListener("keydown", (e) => {
        if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;

        switch (e.code) {
            case "Space":
                e.preventDefault();
                fetch("/api/demo/visitor", { method: "POST" });
                break;
            case "KeyS":
                fetch("/api/demo/mitm", { method: "POST" });
                break;
            case "KeyQ":
                qrModal.classList.toggle("hidden");
                break;
            case "KeyP":
                btnToggleHallway.click();
                break;
            case "KeyM":
                btnToggleAudio.click();
                break;
            case "KeyF":
                btnFullscreen.click();
                break;
            case "KeyR":
                btnResetRoom.click();
                break;
            case "Escape":
                qrModal.classList.add("hidden");
                fullScreenAlert.classList.add("hidden");
                break;
        }
    });

    // Iniciar Dashboard
    startClock();
    initNetworkInfo();
    connectWebSocket();
});
