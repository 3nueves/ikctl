#!/bin/bash

# Make sure that these settings match the desired target cluster settings. To see the settings of an existing cluster use:


kubectl get cm kubeadm-config -n kube-system -o=jsonpath="{.data.ClusterConfiguration}"

# The following example will generate a kubeconfig file with credentials valid for 24 hours for a new user johndoe that is part of the appdevs group:

kubeadm kubeconfig user --config example.yaml --org appdevs --client-name manuelgomez --validity-period 672h

kubeadm kubeconfig user --config manuelgomez.yaml --org invisiblebits --client-name manuelgomez --validity-period 672h

kubeadm kubeconfig user --config eliottgarcia.yaml --org invisiblebits --client-name eliottgarcia

# The following example will generate a kubeconfig file with administrator credentials valid for 1 week:

kubeadm kubeconfig user --config example.yaml --client-name admin --validity-period 168h

kubectl apply -f kits/add_user_kubernetes/RoleBinding.yaml