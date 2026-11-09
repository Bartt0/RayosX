@echo off
title Rayos X del Wi-Fi Publico - Servidor SOC
cd /d "%~dp0"
echo ==============================================================
echo    Iniciando Laboratorio Rayos X del Wi-Fi Publico...
echo ==============================================================
".venv\Scripts\python.exe" iniciar.py
pause

