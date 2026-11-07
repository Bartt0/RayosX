# server/crypto_lab.py
import hashlib
import os
import base64

def process_mitm_payload(mode: str, content: str, alias: str):
    """
    Procesa el envío según el modo seleccionado por el visitante:
    - inseguro (HTTP / Botón Rojo)
    - cifrado (HTTPS / Botón Verde)
    """
    if mode == "inseguro":
        return {
            "mode": "plain",
            "payload_preview": content or "Dato sin cifrar",
            "cipher_hex": None,
            "sha256": None,
            "risk_level": "CRÍTICO - EXPUESTO EN TEXTO PLANO"
        }
    else:
        # Simulación de cifrado real AES-256-CBC y hash SHA-256
        data_bytes = (content or "DatoSecreto").encode('utf-8')
        aes_simulated = base64.b64encode(os.urandom(16)).decode('utf-8') + "#71c*e40b"
        sha_hash = hashlib.sha256(data_bytes).hexdigest()
        
        return {
            "mode": "encrypted",
            "payload_preview": "******** (BLINDADO)",
            "cipher_hex": f"AES: {aes_simulated}",
            "sha256": sha_hash,
            "risk_level": "SEGURO - CONFIDENCIALIDAD GARANTIZADA"
        }