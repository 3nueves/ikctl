#!/bin/bash
#
# Delfos Forwarder
# Compatible with Linux x64 SYSTEMD based systems

# Installation must be run as root
if ! [ $(id -u) = 0 ]
then
   echo "\nInstallation must be run as root\n"
   exit 1
fi

# upload version

if ! [ -f /etc/os-release ]
then
  echo "File os-release not found"
  exit 1
fi  

source /etc/os-release

echo "\n-=[ Delfos Forwarder installation\n"

apt-get update
apt install -y curl sudo ntp apt-transport-https gnupg gnupg1 gnupg2
test $ID = "debian" && curl -fsSL https://toolbelt.treasuredata.com/sh/install-debian-bullseye-td-agent4.sh | sh
test $ID = "ubuntu" && curl -fsSL https://toolbelt.treasuredata.com/sh/install-ubuntu-focal-td-agent4.sh | sh
/opt/td-agent/bin/fluent-gem install fluent-plugin-beats --no-document
mkdir -p /opt/buffer
chmod 777 /opt/buffer

mv .ikctl/forwarder.conf  /etc/td-agent/td-agent.conf

# mkdir /etc/td-agent/certs

# mv .ikctl/cacert.pem      /etc/td-agent/certs/cacert.pem
# mv .ikctl/client-cert.pem /etc/td-agent/certs/client-cert.pem
# mv .ikctl/client-key.pem  /etc/td-agent/certs/client-key.pem
# mv .ikctl/server-key.pem  /etc/td-agent/certs/server-key.pem
# mv .ikctl/server-cert.pem  /etc/td-agent/certs/server-cert.pem

# chmod 755 -R /etc/td-agent/certs

systemctl enable td-agent && systemctl restart td-agent

echo "\n[+] Installation completed\n"