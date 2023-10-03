#!/bin/bash
# invisiblebits.com
# v1.0 by David Moya

## Install kubernetes using kubeadm tool

echo -e "\e[34mStarting installation kubernetes\e[0m\n"

echo -e "\e[34mSet variables\e[32m\n"
POD_NETWORK="10.244.0.0/16"
KUBERNETES_VERSION="1.27.1"
CONTROL_PLANE_ENDPOINT="endpoint-kubes.test.lan:6443"
APISERVER_CERT_EXTRA_SANS="k8s.test.co,k8s-test.lan,k8s.test.com"
TOKEN="5hgvhg.25o3398nu4yglzw7"

echo -e "\n\e[34mInit kubeadm\e[32m\n"

sudo kubeadm init \
    --pod-network-cidr=$POD_NETWORK_CIDR \
    --kubernetes-version=$KUBERNETES_VERSION \
    --control-plane-endpoint=$CONTROL_PLANE_ENDPOINT \
    --apiserver-cert-extra-sans=$APISERVER_CERT_EXTRA_SANS \
    --token=$TOKEN \
    --upload-certs 

echo -e "\n\e[34mInstall admin.conf to root and kub\e[32m\n"

# root user
sudo mkdir /root/.kube
sudo cp /etc/kubernetes/admin.conf /root/.kube/config

# kub user
sudo mkdir /home/kub/.kube
sudo cp /etc/kubernetes/admin.conf /home/kub/.kube/config
sudo chown kub. /home/kub/.kube/ -R


# echo -e "\n\e[34mEnable monitoring to kube-controller-manager, kube-scheduler and etcd\e[32m\n"
# sed -e "s/- --bind-address=127.0.0.1/- --bind-address=0.0.0.0/" -i /etc/kubernetes/manifests/kube-controller-manager.yaml
# sed -e "s/- --bind-address=127.0.0.1/- --bind-address=0.0.0.0/" -i /etc/kubernetes/manifests/kube-scheduler.yaml
# sed -e "s|- --listen-metrics-urls=http://127.0.0.1:2381|- --listen-metrics-urls=http://127.0.0.1:2381,http://0.0.0.0:2381|" -i /etc/kubernetes/manifests/etcd.yaml

echo -e "\n\e[34mFinish\e[0m\n"
