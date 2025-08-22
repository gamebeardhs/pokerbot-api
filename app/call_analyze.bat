@echo off
set URL=http://localhost:5000/api/solver/nhle_decide
curl -sS -X POST "%URL%" ^
  -H "Content-Type: application/json" ^
  --data-binary @payload-real.json
echo(
pause
