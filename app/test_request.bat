@echo off
set URL=http://127.0.0.1:5000/decide
curl -sS -X POST "%URL%" ^
  -H "Content-Type: application/json" ^
  --data-binary @payload.json
echo(
pause