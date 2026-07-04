#!/bin/bash

#bin/logstash -f config/logstash.conf

# Delfos Linux Agent
# Compatible with Linux x64 SYSTEMD based systems

# Installation must be run as root
if ! [ $(id -u) = 0 ]
then
   echo "\nInstallation must be run as root\n"
   exit 1
fi

echo "\n-=[ Delfos Linux Forward installation\n"

INSTALLDIR=`pwd`
HOSTNAME=`hostname`

# Creation of systemd service
echo """[Unit]
Description=Delfos Linux Forward
After=network.target
StartLimitIntervalSec=0

[Service]
WorkingDirectory=$INSTALLDIR
Type=simple
Restart=always
RestartSec=1
User=root
ExecStart=$INSTALLDIR/bin/logstash -f $INSTALLDIR/config/logstash.conf

[Install]
WantedBy=multi-user.target
""" >/etc/systemd/system/delfos-linux-forward.service

# Systemd configuration
systemctl enable delfos-linux-forward 2>/dev/null
systemctl start delfos-linux-forward

echo "\n[+] Installation completed and forward started. Current status:\n"
STATUS=`service delfos-linux-forward status|grep Active`
echo "$STATUS"
echo "\n[+] You can manage this Service with:\n\nservice delfos-linux-forward { stop | start | restart | status }\n"
echo "Happy logging\n"
