#!/bin/bash
# invisiblebits.com
# v3.0 by David Moya

echo -e "\e[34mStarting installation cri-o, kubeadm, kubelet and kubectl\e[0m\n"

echo -e "\e[34mSet variables\e[0m\n"

export KUBERNETES_VERSION="1.27.1-00"

echo -e "\n\e[34mInstall package we will need\e[32m\n"
sudo apt update && sudo apt install -y curl gnupg gnupg2 gnupg1

echo -e "\n\e[34mDisable swap\e[32m\n"
sudo touch /etc/rc.local
sudo chmod +x /etc/rc.local

cat  <<EOF | sudo tee /etc/rc.local
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

# Force disable swap
sudo swapoff -a

echo -e "\n\e[34mPrepare Install\e[32m\n"

echo -e "\n\e[34mConfig sysctl\e[32m\n"
cat <<EOF | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.ipv4.ip_forward                 = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

sudo sysctl --system

echo -e "\n\e[34mInstall kubeadm kubelet kubectl\e[32m\n"

sudo apt-get update && sudo apt-get install -y apt-transport-https curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list	
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF

sudo apt-get update
# export KUBERNETES_VERSION="1.24.0-00"; 
sudo apt-get install -y -V \
	kubeadm=$KUBERNETES_VERSION \
	kubelet=$KUBERNETES_VERSION \
	kubectl=$KUBERNETES_VERSION

sudo apt-mark hold kubelet kubeadm kubectl

sudo systemctl daemon-reload
sudo systemctl restart kubelet

echo -e "\n\e[34mFinish Install\e[0m\n"