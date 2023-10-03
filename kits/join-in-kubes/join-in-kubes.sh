#!/bin/bash
# invisiblebits.com
# v1.0 by David Moya

echo -e "\e[34mJoin worker in kubernetes\e[0m\n"

echo -e "\e[34mInstall sshpass\e[32m\n"
apt-get update && apt-get install -y sshpass

echo -e "\e[34mSet variables\e[32m\n"

export PASS=$1

token=$(sshpass -p "$PASS" ssh -o 'StrictHostKeyChecking=no' kub@master-1.test.co 'kubeadm token create --print-join-command')
# token=$(sshpass -p "$PASS" ssh -o 'StrictHostKeyChecking=no' kub@master-kubes01.ibits.lan 'kubeadm token create --print-join-command')

echo -e "\e[34mExec join\e[32m\n"
echo $token | bash

echo -e "\n\e[34mFinish join process\e[0m\n"

