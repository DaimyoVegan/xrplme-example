#!/bin/bash
# Start all 5 APAC country bot servers
cd /opt/xrplme/thoughts/api

# Define countries: module_name, port, display
COUNTRIES=(
  "brunei:8111:Brunei"
  "laos:8112:Laos"
  "myanmar:8113:Myanmar"
  "timor_leste:8114:Timor-Leste"
  "papua_new_guinea:8115:Papua New Guinea"
)

for entry in "${COUNTRIES[@]}"; do
  IFS=":" read -r module port display <<< "$entry"
  log_file="/tmp/${module}.log"
  
  # Check if already running
  if curl -s "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
    echo "$display (port $port): Already running"
  else
    echo "Starting $display (port $port)..."
    nohup /home/xrpladmin/thailand_bot_venv/bin/python -m uvicorn ${module}_bot_server:app --host 127.0.0.1 --port $port > "$log_file" 2>&1 &
    PID=$!
    echo "  PID: $PID, Log: /tmp/${module}.log"
    sleep 2
  fi
done

# Wait for all to start
sleep 5

echo ""
echo "=== Verification ==="
for entry in "${COUNTRIES[@]}"; do
  IFS=":" read -r module port display <<< "$entry"
  health=$(curl -s "http://127.0.0.1:$port/health" 2>&1)
  records=$(echo "$health" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data_records',0))" 2>/dev/null || echo "0")
  bot_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:$port/api/v1/${module}/bot" -H "Content-Type: application/json" -d "{\"message\":\"test\",\"session_id\":\"t\"}" 2>/dev/null)
  echo "  $display: port=$port, health_records=$records, bot_endpoint=HTTP $bot_code"
done
