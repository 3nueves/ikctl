#!/bin/bash
# deploy-service.sh
# Deploys a service on the server.
#
# Parameters (passed from pipeline):
#   $1 - APP_VERSION  : version to deploy (from CLI param)
#   $2 - SERVER_HOST  : hostname from previous step (from steps.prepare-env.HOSTNAME)
#
# Outputs (KEY=VALUE) consumed by configure-monitoring:
#   SERVICE_PORT
#   SERVICE_URL
#   SERVICE_STATUS
set -e

APP_VERSION="${1:-latest}"
SERVER_HOST="${2:-$(hostname -s)}"
SERVICE_PORT=8080

echo "==> Deploying service version $APP_VERSION on $SERVER_HOST..."

# Install the service (example with a simple Python HTTP server)
mkdir -p /opt/myservice
cat > /opt/myservice/app.py <<EOF
import http.server, socketserver
PORT = $SERVICE_PORT
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
EOF

# Create systemd service
cat > /etc/systemd/system/myservice.service <<EOF
[Unit]
Description=My Service $APP_VERSION
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/myservice/app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable myservice
systemctl start myservice

# Verify it started
sleep 2
if systemctl is-active --quiet myservice; then
    STATUS="running"
    echo "==> Service running on port $SERVICE_PORT"
else
    STATUS="failed"
    echo "==> ERROR: Service failed to start" >&2
    exit 1
fi

# Output variables for configure-monitoring step
echo "SERVICE_PORT=$SERVICE_PORT"
echo "SERVICE_URL=http://$SERVER_HOST:$SERVICE_PORT"
echo "SERVICE_STATUS=$STATUS"
