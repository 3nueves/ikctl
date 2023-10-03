#!/bin/bash

echo -e "## Starting installation-----------------------------\n"

sudo apt update -y && sudo apt install -y vim sudo net-tools

echo -e "## Set variables-------------------------------------\n"

DOCKER_CE_VERSION="5:20.10.18~3-0~debian-buster"
DOCKER_CE_CLI_VERSION="5:20.10.18~3-0~debian-buster"
CONTAINER_IO_VERSION="1.6.8-1"

echo -e "## Config sysctl------------------------------------------------------------\n"

cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

sudo sysctl --system

# Make sure that the br_netfilter module is loaded before this step
sudo modprobe br_netfilter


echo -e "## Install Docker CE---------------------------------------------------------\n"

sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common gnupg2

# Add Docker’s official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker apt repository.
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian buster stable" -y

DOCKER_CE_VERSION="5:19.03.12~3-0~debian-buster" && \
DOCKER_CE_CLI_VERSION="5:19.03.12~3-0~debian-buster" && \
CONTAINER_IO_VERSION="1.2.13-2" && \
sudo apt-get update && \
sudo apt-get install -y \
    containerd.io=${CONTAINER_IO_VERSION} \
    docker-ce=${DOCKER_CE_VERSION} \
    docker-ce-cli=${DOCKER_CE_CLI_VERSION}

# Setup docker daemon.
sudo mkdir -p /etc/docker/
cat <<EOF | sudo tee /etc/docker/daemon.json
{
"exec-opts": ["native.cgroupdriver=systemd"],
"log-driver": "json-file",
"log-opts": {
"max-size": "100m"
},
"storage-driver": "overlay2",
"default-ulimits": {
	"nofile": {
		"Name": "memlock",
		"Hard": -1,
		"Soft": -1 
	}
}
}
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker
sudo systemctl enable docker