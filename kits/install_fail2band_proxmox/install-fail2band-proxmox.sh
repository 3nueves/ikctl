#!/bin/bash

apt install fail2ban -y

cat <<EOF > /etc/fail2ban/jail.local
[ssh]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
# 1 hour
bantime = 3600
ignoreip = 127.0.0.1,10.0.0.30,10.0.0.31,10.0.0.32
EOF