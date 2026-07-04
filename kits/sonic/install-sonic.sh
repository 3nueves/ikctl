#!/bin/bash

echo -e "Create user sonic\n"
adduser --home /home/sonic --shell /bin/bash --uid 10011 --disabled-password --gecos GECOS sonic

echo -e "Create folder bin\n"
mkdir /home/sonic/bin

echo -e "Copy binary file and env to foler bin\n"
cp /home/kub/.ikctl/sonic_forwarder /home/sonic/bin
cp /home/kub/.ikctl/forwarder.env /home/sonic/bin

echo -e "Grant permisions to user sonic to execute binery"
chown sonic. /home/sonic/bin  -R
chmod +x /home/sonic/bin/sonic_forwarder

echo -e "Creation of systemd service\n"
echo """[Unit]
Description=Service to update config file td-agent
After=network.target
StartLimitIntervalSec=0

[Service]
WorkingDirectory=/home/sonic
Type=simple
Restart=always
RestartSec=1
User=sonic
ExecStart=/home/sonic/bin/sonic_forwarder

[Install]
WantedBy=multi-user.target
""" >/etc/systemd/system/sonic-forward.service

systemctl daemon-reload
systemctl start sonic-forwarder.service
systemctl status sonic-forwarder.service