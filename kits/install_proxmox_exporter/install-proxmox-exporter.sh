#!/bin/bash

groupadd -g 10022 prometheus && useradd -u 10022 -g 10022 prometheus && usermod -s /dev/null prometheus

apt install python3-venv -y

python3 -m venv /opt/prometheus-pve-exporter

/opt/prometheus-pve-exporter/bin/pip install prometheus-pve-exporter

mkdir -p /etc/prometheus
cat <<EOF > /etc/prometheus/pve.yml
default:
    user: exporter_prometheus@pve
    token_name: "exporter_metrics"
    token_value: "479ffa2f-9d35-4643-8239-8c24e8376eec"
    verify_ssl: false
EOF

cat <<EOF > /etc/systemd/system/prometheus-pve-exporter.service
[Unit]
Description=Prometheus exporter for Proxmox VE
Documentation=https://github.com/znerol/prometheus-pve-exporter

[Service]
Restart=always
User=prometheus
ExecStart=/opt/prometheus-pve-exporter/bin/pve_exporter /etc/prometheus/pve.yml

[Install]
WantedBy=multi-user.target
EOF


systemctl daemon-reload
systemctl start prometheus-pve-exporter