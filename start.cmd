@echo off
rem Starts SafeRoute (backend + tunnels + Expo). See start.ps1 for the options.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
