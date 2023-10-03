#!/bin/bash
# invisiblebits.com
# v1.0 by David Moya

echo -e "\e[34mStarting install CNI to kubernetes\e[0m\n"
echo -e "referece https://projectcalico.docs.tigera.io/getting-started/kubernetes/self-managed-onprem/onpremises#install-calico-with-kubernetes-api-datastore-50-nodes-or-less\n"

echo -e "\n\e[34mDownload and keep calico manifest\e[32m\n"
mkdir /etc/kubernetes/network
curl https://raw.githubusercontent.com/projectcalico/calico/v3.25.1/manifests/calico.yaml -o /etc/kubernetes/network/calico.yaml

echo -e "\n\e[34mDeploy and install calico\e[32m\n"
kubectl apply -f /etc/kubernetes/network/calico.yaml --kubeconfig=/etc/kubernetes/admin.conf

echo -e "\n\e[34mFinish install calico\e[0m\n"

