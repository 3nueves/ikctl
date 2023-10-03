#!/bin/bash
# invisiblebits.com
# v1.0 by David Moya

IP=$(ifconfig | grep 172.31.41 | awk '{print $2}')

case $IP in

  "172.31.41.48")
    hostnamectl set-hostname test
    echo "172.31.41.48 test" >> /etc/hosts
    ;;
  *)
    echo -n "unknown"
    ;;
esac


        