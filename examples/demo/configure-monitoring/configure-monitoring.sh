#!/bin/bash
# configure-monitoring.sh
# Configures monitoring for a deployed service.
#
# Parameters (from pipeline):
#   $1 - SERVICE_URL   : URL of the service to monitor (from steps.deploy-service.SERVICE_URL)
#   $2 - SERVICE_PORT  : Port of the service (from steps.deploy-service.SERVICE_PORT)
#   $3 - ALERT_EMAIL   : Email for alerts (from CLI param)
set -e

SERVICE_URL="${1:-http://localhost:8080}"
SERVICE_PORT="${2:-8080}"
ALERT_EMAIL="${3:-ops@example.com}"
MONITOR_PORT=9090

echo "==> Configuring monitoring for $SERVICE_URL"
echo "==> Alerts will be sent to: $ALERT_EMAIL"

# Install monitoring tools
apt-get install -y -qq prometheus-node-exporter 2>/dev/null || true

# Write monitoring config
mkdir -p /etc/monitoring
cat > /etc/monitoring/targets.json <<EOF
[
  {
    "targets": ["localhost:$SERVICE_PORT"],
    "labels": {
      "job": "myservice",
      "service_url": "$SERVICE_URL"
    }
  }
]
EOF

cat > /etc/monitoring/alerts.conf <<EOF
ALERT_EMAIL=$ALERT_EMAIL
SERVICE_URL=$SERVICE_URL
EOF

echo "==> Monitoring configured successfully"
echo "==> Target: $SERVICE_URL"

# Output for pipeline summary
echo "MONITOR_ENDPOINT=http://$(hostname -s):$MONITOR_PORT"
echo "ALERT_EMAIL=$ALERT_EMAIL"
