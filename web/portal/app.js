// web/portal/app.js
document.addEventListener("DOMContentLoaded", () => {
    let assignedNodeId = null;

    // 1. Recolección de Huella Digital del Teléfono
    function collectClientFingerprint() {
        const ua = navigator.userAgent;
        let os = "Dispositivo Móvil";
        if (/android/i.test(ua)) os = "Android OS";
        else if (/iphone|ipad|ipod/i.test(ua)) os = "Apple iOS";
        else if (/windows/i.test(ua)) os = "Windows";
        else if (/mac os|macintosh/i.test(ua)) os = "macOS";
        else if (/linux/i.test(ua)) os = "Linux";

        let browser = "Navegador Web";
        if (/edg/i.test(ua)) browser = "Microsoft Edge";
        else if (/samsungbrowser/i.test(ua)) browser = "Samsung Internet";
        else if (/chrome|crios/i.test(ua)) browser = "Google Chrome";
        else if (/safari/i.test(ua)) browser = "Apple Safari";
        else if (/firefox|fxios/i.test(ua)) browser = "Mozilla Firefox";

        // Obtener GPU mediante WebGL si el navegador lo permite
        let gpu = "Estándar Móvil";
        try {
            const canvas = document.createElement("canvas");
            const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
            if (gl) {
                const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
                if (debugInfo) {
                    gpu = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                }
            }
        } catch (e) {
            gpu = "Protegido por Sandbox";
        }

        const screenRes = `${window.screen.width} x ${window.screen.height}`;
        const cpuCores = navigator.hardwareConcurrency || "4";

        return {
            os: os,
            browser: browser,
            screen: screenRes,
            cpu_cores: cpuCores,
            gpu: gpu,
            language: navigator.language || "es"
        };
    }

    // 2. Registro con el Backend para obtener el ID de Nodo
    async function registerDevice() {
        const fp = collectClientFingerprint();

        document.getElementById("osVal").textContent = fp.os;
        document.getElementById("browserVal").textContent = fp.browser;
        document.getElementById("screenVal").textContent = fp.screen;
        document.getElementById("cpuVal").textContent = `${fp.cpu_cores} núcleos de procesamiento`;
        document.getElementById("gpuVal").textContent = fp.gpu;

        try {
            const response = await fetch("/api/connect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(fp)
            });

            if (response.ok) {
                const data = await response.json();
                assignedNodeId = data.node_id;
                document.getElementById("nodeBadge").textContent = `TU DISPOSITIVO ES EL NODO: ${assignedNodeId}`;
                document.getElementById("ipVal").textContent = data.ip_masked || "192.168.1.***";
            } else {
                fallbackConnection();
            }
        } catch (err) {
            console.warn("Servidor en modo contingencia:", err);
            fallbackConnection();
        }
    }

    function fallbackConnection() {
        assignedNodeId = "#01";
        document.getElementById("nodeBadge").textContent = "DISPOSITIVO CONECTADO (NODO #01)";
        document.getElementById("ipVal").textContent = "192.168.1.***";
    }

    // 3. Laboratorio MitM: Envío de prueba
    async function transmitMitm(mode) {
        const alias = document.getElementById("aliasInput").value.trim() || "participante_demo";
        const password = document.getElementById("passInput").value.trim() || "ClavePrueba123!";
        const resultBox = document.getElementById("mitmResult");
        const resultTitle = document.getElementById("resultTitle");
        const resultContent = document.getElementById("resultContent");

        resultBox.classList.remove("hidden", "alert-red", "alert-green");

        try {
            const response = await fetch("/api/transmit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    node_id: assignedNodeId || "#01",
                    mode: mode,
                    alias: alias,
                    secret: password
                })
            });

            if (response.ok) {
                const res = await response.json();
                renderResult(mode, res);
            } else {
                renderLocalFallback(mode, alias, password);
            }
        } catch (err) {
            renderLocalFallback(mode, alias, password);
        }
    }

    function renderResult(mode, res) {
        const resultBox = document.getElementById("mitmResult");
        const resultTitle = document.getElementById("resultTitle");
        const resultContent = document.getElementById("resultContent");

        if (mode === "plain") {
            resultBox.classList.add("alert-red");
            resultTitle.textContent = "🚨 ¡ALERTA! TUS DATOS FUERON INTERCEPTADOS";
            resultContent.textContent = 
`[REPORTE DE INTERCEPCIÓN EN VIVO]
ESTADO     : PELIGRO - EXPUESTO EN TEXTO PLANO
DISPOSITIVO: ${assignedNodeId || "#01"}
USUARIO    : ${res.alias}
CONTRASEÑA : ${res.secret}

DATOS QUE CAPTURÓ EL ATACANTE EN EL AIRE:
${res.payload_preview}

EXPLICACIÓN:
Al no usar cifrado HTTPS, cualquier persona conectada a la misma red
Wi-Fi pudo capturar tu usuario y tu contraseña exactamente como los
escribiste. Revisa la pantalla gigante del monitor para ver la alerta.`;
        } else {
            resultBox.classList.add("alert-green");
            resultTitle.textContent = "🛡️ ¡ÉXITO! CONEXIÓN BLINDADA CON CIFRADO";
            resultContent.textContent = 
`[REPORTE DE BLINDAJE CRIPTOGRÁFICO]
ESTADO     : SEGURO - TÚNEL TLS 1.3 / AES-256
DISPOSITIVO: ${assignedNodeId || "#01"}
ALIAS      : ${res.alias} (Registrado en el Muro Protegido)
CONTRASEÑA : •••••••••••••••• (TOTALMENTE ILEGIBLE)

BLOQUE CIFRADO QUE VIAJÓ POR EL WI-FI (HEX):
${res.cipher_hex}

HASH DE INTEGRIDAD (SHA-256):
${res.sha256}

EXPLICACIÓN:
Aunque un atacante capture tus paquetes de red, solo verá caracteres
aleatorios sin sentido matemático. Tu información está 100% a salvo.`;
        }
    }

    function renderLocalFallback(mode, alias, password) {
        const resultBox = document.getElementById("mitmResult");
        const resultTitle = document.getElementById("resultTitle");
        const resultContent = document.getElementById("resultContent");

        if (mode === "plain") {
            resultBox.classList.add("alert-red");
            resultTitle.textContent = "🚨 ¡ALERTA! TEXTO PLANO CAPTURADO";
            resultContent.textContent = `Usuario: ${alias}\nContraseña: ${password}\n¡Peligro! Tus datos se transmitieron sin cifrar.`;
        } else {
            resultBox.classList.add("alert-green");
            resultTitle.textContent = "🛡️ ¡BLINDADO CON CIFRADO AES-256!";
            resultContent.textContent = `Usuario: ${alias}\nContraseña: [PROTEGIDA]\nHex: 17 03 03 00 30 7B E4 91 AC 55...\nHash SHA-256: 8f434346648f...`;
        }
    }

    // Botones de autocompletado rápido
    document.getElementById("btnFillAlice").addEventListener("click", () => {
        document.getElementById("aliasInput").value = "juan_perez";
        document.getElementById("passInput").value = "MiClaveSegura2026!";
    });
    document.getElementById("btnFillBob").addEventListener("click", () => {
        document.getElementById("aliasInput").value = "sofia_admin";
        document.getElementById("passInput").value = "AdminRoot#99$";
    });
    document.getElementById("btnFillCard").addEventListener("click", () => {
        document.getElementById("aliasInput").value = "banco_usuario";
        document.getElementById("passInput").value = "PIN_Transferencia_8891";
    });

    // Listeners de los botones de envío
    document.getElementById("btnPlain").addEventListener("click", () => transmitMitm("plain"));
    document.getElementById("btnEncrypted").addEventListener("click", () => transmitMitm("encrypted"));

    // Inicializar al cargar
    registerDevice();
});
