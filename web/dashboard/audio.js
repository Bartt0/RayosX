/**
 * audio.js - Sintetizador de Efectos de Sonido con Web Audio API pura.
 * 100% Offline: Genera ondas senoidales, armónicos y ruidos sin dependencias externas ni archivos de audio.
 */

class SocAudioSynthesizer {
    constructor() {
        this.ctx = null;
        this.isMuted = false;
        this.init();
    }

    init() {
        // Inicialización diferida por políticas de autoplay de navegadores modernos
        const unlock = () => {
            if (!this.ctx) {
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (AudioCtx) {
                    this.ctx = new AudioCtx();
                }
            }
            if (this.ctx && this.ctx.state === "suspended") {
                this.ctx.resume();
            }
            window.removeEventListener("click", unlock);
            window.removeEventListener("keydown", unlock);
        };
        window.addEventListener("click", unlock);
        window.addEventListener("keydown", unlock);
    }

    ensureContext() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) this.ctx = new AudioCtx();
        }
        if (this.ctx && this.ctx.state === "suspended") {
            this.ctx.resume();
        }
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        if (!this.isMuted) {
            this.playSonar(); // Confirmación auditiva
        }
        return this.isMuted;
    }

    // 1. Sonar de Radar al unirse un nuevo nodo (Ping armónico)
    playSonar() {
        if (this.isMuted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = "sine";
        osc.frequency.setValueAtTime(880, now); // A5
        osc.frequency.exponentialRampToValueAtTime(1760, now + 0.15); // A6

        gain.gain.setValueAtTime(0.18, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.5);
    }

    // 2. Alarma de Intercepción Crítica (Sirena Roja Texto Plano)
    playPlainAlert() {
        if (this.isMuted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        
        // Oscilador de frecuencia modulada para sirena de intrusión
        for (let i = 0; i < 3; i++) {
            const t = now + (i * 0.18);
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = "sawtooth";
            osc.frequency.setValueAtTime(550, t);
            osc.frequency.linearRampToValueAtTime(950, t + 0.09);
            osc.frequency.linearRampToValueAtTime(450, t + 0.18);

            gain.gain.setValueAtTime(0.25, t);
            gain.gain.exponentialRampToValueAtTime(0.01, t + 0.17);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(t);
            osc.stop(t + 0.18);
        }
    }

    // 3. Escudo Protector Cifrado (Acorde Mayor Armónico Verde)
    playEncryptedShield() {
        if (this.isMuted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const chord = [523.25, 659.25, 783.99, 1046.50]; // Do, Mi, Sol, Do (C Mayor armónico)

        chord.forEach((freq, idx) => {
            const delay = idx * 0.05;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = "triangle";
            osc.frequency.setValueAtTime(freq, now + delay);

            gain.gain.setValueAtTime(0.12, now + delay);
            gain.gain.exponentialRampToValueAtTime(0.001, now + delay + 0.6);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now + delay);
            osc.stop(now + delay + 0.65);
        });
    }

    // 4. Tick sutil de telemetría / consola
    playTick() {
        if (this.isMuted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = "sine";
        osc.frequency.setValueAtTime(2400, now);

        gain.gain.setValueAtTime(0.03, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.05);
    }
}

// Instancia global
window.socAudio = new SocAudioSynthesizer();

