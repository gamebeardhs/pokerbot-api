@echo off
set URL=http://127.0.0.1:8000/decide?strategy_name=default_cash6max

REM Make sure payload_pre.json exists in the same directory as this .bat
curl -sS -X POST "%URL%" ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer devtoken" ^
  --data-binary @payload_pre.json

echo(
pause
