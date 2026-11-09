# server/crypto_lab.py
import hashlib
import os
import binascii
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from typing import Dict, Any

def process_mitm_payload(mode: str, content: str, alias: str) -> Dict[str, Any]:
    """
    Simulador de intercepción Man-in-the-Middle (MitM):
    - Modo Inseguro ('plain' o 'inseguro'): El paquete viaja en texto plano sin cifrar vía HTTP.
      Cualquier nodo en la red Wi-Fi o atacante con ARP spoofing puede leerlo íntegro.
    - Modo Blindado ('encrypted' o 'cifrado'): El paquete se cifra localmente con AES-256-CBC
      y se protege dentro de un túnel TLS 1.3 con comprobación de integridad SHA-256.
    """
    mode_normalized = "encrypted" if mode in ["encrypted", "cifrado", "blindado"] else "plain"
    secret_text = content or "Credencial_123"
    alias_clean = alias or "visitante_anonimo"

    if mode_normalized == "plain":
        # Simulación de paquete HTTP capturado en claro por un sniffer
        http_packet_preview = (
            f"POST /api/login HTTP/1.1\r\n"
            f"Host: portal-inseguro.local\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n\r\n"
            f"user={alias_clean}&password={secret_text}"
        )
        return {
            "mode": "plain",
            "alias": alias_clean,
            "secret": secret_text,
            "payload_preview": http_packet_preview,
            "cipher_hex": None,
            "sha256": None,
            "risk_level": "CRÍTICO - INTERCEPTADO EN TEXTO PLANO",
            "status": "EXPOSED"
        }
    else:
        # Cifrado real AES-256-CBC con cryptography
        key = os.urandom(32)  # 256 bits
        iv = os.urandom(16)   # 128 bits
        
        # Padding PKCS7
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(secret_text.encode('utf-8')) + padder.finalize()
        
        # Cifrador AES CBC
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Simulación de cabecera TLS 1.3 Record (0x17 = Application Data, 0x0303 = TLS 1.2/1.3)
        tls_header = bytes([0x17, 0x03, 0x03, 0x00, len(iv) + len(ciphertext)])
        full_packet = tls_header + iv + ciphertext
        cipher_hex = binascii.hexlify(full_packet).decode('utf-8').upper()
        
        # Formatear el hex con espacios cada 2 bytes para legibilidad tipo Wireshark
        formatted_hex = " ".join([cipher_hex[i:i+2] for i in range(0, min(len(cipher_hex), 64), 2)])
        if len(cipher_hex) > 64:
            formatted_hex += " ... [TRUNCATED 256-BIT]"

        # Hash SHA-256 de integridad
        sha_hash = hashlib.sha256(secret_text.encode('utf-8')).hexdigest()

        return {
            "mode": "encrypted",
            "alias": alias_clean,
            "secret": "•" * len(secret_text),
            "payload_preview": "TLS 1.3 Application Data [AES-256-CBC Ciphertext]",
            "cipher_hex": formatted_hex,
            "sha256": sha_hash,
            "risk_level": "SEGURO - TÚNEL CIFRADO INQUEBRANTABLE",
            "status": "PROTECTED"
        }
