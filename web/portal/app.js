document.addEventListener("DOMContentLoaded", () => {
    let assignedNodeId = null;

    // 1. Recolectar metadatos del cliente
    function collectFingerprint() {
        const ua = navigator.userAgent;
        let os = "Desconocido";
        if (/android/i.test(ua)) os = "Android";
        else if (/iphone|ipad|ipod/i.test(ua)) os = "iOS";
        else if (/windows/i.test(ua)) os = "Windows";
        else if (/mac os/i.test(ua)) os = "macOS";
        else if (/linux/i.test(ua)) os = "Linux";

        let browser = "Desconocido";
        if (/chrome|crios/i.test(ua)) browser = "Chrome";
        else if (/safari/i.test(ua) && !/chrome/i.test(ua)) browser = "Safari";
        else if (/firefox|fxios/i.test(ua)) browser = "Firefox";
        else if (/edg/i.test(ua)) browser = "Edge";

        // Obtener GPU mediante WebGL si está disponible
        let gpu = "No disponible";
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
            gpu = "Restringido";
        }

        return {
            os: os,
            browser: browser,
            screen: `${window.screen.width}x${window.screen.height} (DPR: ${window.devicePixelRatio})`,
            cpu_cores: navigator.hardwareConcurrency || "N/D",
            gpu: gpu,
            language: navigator.language || "es"
        };
    }

    // 2. Registrar conexión en el backend
    async function registerVisitor() {
        const fp = collectFingerprint();
        
        // Actualizar UI local preliminar
        document.getElementById("osVal").textContent = fp.os;
        document.getElementById("browserVal").textContent = fp.browser;
        document.getElementById("screenVal").textContent = fp.screen;
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
                document.getElementById("nodeBadge").textContent = `Nodo Asignado: ${assignedNodeId}`;
                if (data.ip_masked) {
                    document.getElementById("ipVal").textContent = data.ip_masked;
                }
            } else {
                document.getElementById("nodeBadge").textContent = "Modo Local / Conectado";
                document.getElementById("ipVal").textContent = "192.168.1.***";
            }
        } catch (err) {
            console.error("Error conectando con el servidor SOC:", err);
            document.getElementById("nodeBadge").textContent = "Modo Demostración";
            document.getElementById("ipVal").textContent = "192.168.1.***";
        }
    }

    // 3. Ejecutar pruebas de transmisión (MitM)
    async function transmitPayload(mode) {
        const alias = document.getElementById("aliasInput").value || "anonimo";
        const password = document.getElementById("passInput").value || "123456";
        const resultContainer = document.getElementById("mitmResult");
        const resultTitle = document.getElementById("resultTitle");
        const resultContent = document.getElementById("resultContent");

        resultContainer.className = "mitm-result";

        try {
            const response = await fetch("/api/transmit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    node_id: assignedNodeId || "#01",
                    mode: mode, // "plain" o "encrypted"
                    alias: alias,
                    secret: password
                })
            });

            if (response.ok) {
                const resData = await response.json();
                resultContainer.classList.remove("hidden");

                if (mode === "plain") {
                    resultContainer.classList.add("alert-red");
                    resultTitle.textContent = "🚨 ¡ALERTA! Interceptado en Texto Plano";
                    resultContent.textContent = `[HTTP INSEGURO CAPTURADO]\nAlias: ${resData.alias}\nPassword: ${resData.secret}\nNivel de riesgo: CRÍTICO (Visible para cualquier atacantre en la misma red Wi-Fi)`;
                } else {
                    resultContainer.classList.add("alert-green");
                    resultTitle.textContent = "🛡️ Tráfico Blindado Correctamente";
                    resultContent.textContent = `[TLS 1.3 + AES-256-CBC]\nPayload Cifrado (Hex):\n${resData.cipher_hex}\nSHA-256 Hash:\n${resData.sha256}\nEstado: Protegido en Muro de Usuarios.`;
                }
            } else {
                alert("Error al procesar la transmisión en el servidor.");
            }
        } catch (err) {
            console.error("Error en MitM:", err);
            // Fallback visual si el servidor no está corriendo aún localmente
            resultContainer.classList.remove("hidden");
            if (mode === "plain") {
                resultContainer.classList.add("alert-red");
                resultTitle.textContent = "🚨 ALERTA (Simulación Local)";
                resultContent.textContent = `Alias: ${alias}\nPassword: ${password}\n¡Expuesto en texto plano!`;
            } else {
                resultContainer.classList.add("alert-green");
                resultTitle.textContent = "🛡️ Blindado (Simulación Local)";
                resultContent.textContent = `AES-256 Hex: a9f8e7d6b5c4... (Protegido)`;
            }
        }
    }

    // Event Listeners
    document.getElementById("btnPlain").addEventListener("click", () => transmitPayload("plain"));
    document.getElementById("btnEncrypted").addEventListener("click", () => transmitPayload("encrypted"));

    // Inicializar registro al cargar
    registerVisitor();
});