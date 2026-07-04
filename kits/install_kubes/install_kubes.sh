#!/bin/bash

echo -e "## Starting installation-----------------------------\n"

apt update -y && apt install -y vim sudo net-tools

echo -e "## Set variables-------------------------------------\n"

KUBEADM_VERSION="1.18.6-00"
KUBELET_VERSION="1.18.6-00"
KUBECTL_VERSION="1.18.6-00"
DOCKER_CE_VERSION="5:19.03.12~3-0~debian-buster"
DOCKER_CE_CLI_VERSION="5:19.03.12~3-0~debian-buster"
CONTAINER_IO_VERSION="1.2.13-2"


echo -e "## Change keyboard----------------------------------\n"

sed -i "s/pc105/pc104/g" /etc/default/keyboard
sed -i "s/gb/es/g" /etc/default/keyboard


echo -e "## Add ssh key------------------------------------------\n"

mkdir -p /home/kub/.ssh/
touch /home/kub/.ssh/authorized_keys
cat /home/kub/id_rsa_kubernetes-unelink.pub >> /home/kub/.ssh/authorized_keys
chown kub. /home/kub/.ssh -R

echo "## add sudores"
cat > /etc/sudoers.d/kub <<EOF
kub ALL=(ALL:ALL) NOPASSWD: ALL
EOF

echo -e "## Disable swap------------------------------------------\n"

touch /etc/rc.local
chmod +x /etc/rc.local

cat > /etc/rc.local <<EOF
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

# added by ADMIN to run fancy stuff at boot:

swapoff -a || exit 1

exit 0
EOF


echo -e "## Config sysctl------------------------------------------------------------\n"

cat <<EOF > /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

sysctl --system

# Make sure that the br_netfilter module is loaded before this step
modprobe br_netfilter


echo -e "## Install Docker CE---------------------------------------------------------\n"

apt-get update && apt-get install -y apt-transport-https ca-certificates curl software-properties-common gnupg2

# Add Docker’s official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

# Add Docker apt repository.
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian buster stable" -y

apt-get update && apt-get install -y \
  containerd.io=$CONTAINER_IO_VERSION \
  docker-ce=$DOCKER_CE_VERSION \
  docker-ce-cli=$DOCKER_CE_CLI_VERSION

# Setup docker daemon.
mkdir -p /etc/docker/
cat > /etc/docker/daemon.json <<EOF
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

systemctl daemon-reload
systemctl restart docker
systemctl enable docker


echo -e "## Install kubeadm kubelet  kubectl---------------------------------\n"

apt-get update && apt-get install -y apt-transport-https curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF

apt-get update
apt-get install -y -V kubeadm=$KUBEADM_VERSION \
	kubelet=$KUBELET_VERSION \
	kubectl=$KUBELET_VERSION

apt-mark hold kubelet kubeadm kubectl

systemctl daemon-reload
systemctl restart kubelet

echo -e "## Finish Install-------------------------------------------