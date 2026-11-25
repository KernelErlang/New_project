@echo off
rem  Nocturne Codex - double-click to open the grimoire (Windows).
setlocal
title Nocturne Codex
cd /d "%~dp0"
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo.
  echo   The Codex needs Python 3.9 or newer, and none was found.
  echo   Install it from https://www.python.org/downloads/
  echo   and tick "Add python.exe to PATH" during the installation.
  echo.
  pause
  exit /b 1
)
%PY% -m nocturne %*
if errorlevel 1 (
  echo.
  echo   The candle guttered. Read the message above, then press a key.
  pause
)
