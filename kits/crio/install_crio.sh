#!/bin/bash
# invisiblebits.com
# v1.0 by David Moya

export CRIO_VERSION="1.27"
export OS="Debian_11"
# export OS="xUbuntu_22.04"

echo -e "\n\e[34mInstall package we will need\e[32m\n"

sudo apt update && sudo apt install -y curl gnupg gnupg2 gnupg1 sudo vim net-tools

echo -e "\n\e[34mCreate /etc/crio directory\e[32m\n"

sudo mkdir -p /etc/crio

echo -e "\n\e[34mCreate the .conf file to load the modules at bootup\e[32m\n"

ECHO=$(echo -e "\n")

cat <<EOF | sudo tee /etc/modules-load.d/crio.conf
overlay
br_netfilter
EOF

sudo modprobe br_netfilter

sudo modprobe overlay

echo -e "\n\e[34mConfig sysctl\e[32m\n"

cat <<EOF | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.ipv4.ip_forward                 = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

sudo sysctl --system

echo -e "\n\e[34mInstall CRI-O\e[32m\n"

# CRIO_VERSION="1.24"; OS="Debian_11"; 
cat <<EOF | sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list
deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/$OS/ /
EOF

# CRIO_VERSION="1.24"; OS="Debian_11"; 
cat <<EOF | sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable:cri-o:$CRIO_VERSION.list
deb http://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable:/cri-o:/$CRIO_VERSION/$OS/ /
EOF

# CRIO_VERSION="1.24"; OS="Debian_11"; 
sudo curl -L https://download.opensuse.org/repositories/devel:kubic:libcontainers:stable:cri-o:$CRIO_VERSION/$OS/Release.key | sudo -E apt-key --keyring /etc/apt/trusted.gpg.d/libcontainers.gpg add -

# CRIO_VERSION="1.24"; OS="Debian_11"; 
sudo curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/$OS/Release.key | sudo -E apt-key --keyring /etc/apt/trusted.gpg.d/libcontainers.gpg add -

sudo apt-get update

sudo apt-get install -y cri-o cri-o-runc

cat <<EOF | sudo tee /etc/crio/crio.conf
[crio]
cgroup_manager = "systemd"
storage_driver = "overlay"
[crio.runtime]
default_ulimits = [ "nofile=262144:262144", "memlock=-1:-1" ]
cgroup_manager = "systemd"
log_size_max = -1
EOF

sudo systemctl daemon-reload

sudo systemctl enable crio --now
