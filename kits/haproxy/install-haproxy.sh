#!/bin/bash
# v1.0 by David Moya to invisible bits
# Install haproxy

echo -e "Starting installation\n"

echo -e "Set variables\n"

# Inject variables
export IP_MASTER_1="10.60.0.1"
export IP_MASTER_2="10.60.0.4"
export IP_MASTER_3="10.60.0.3"
export VERSION="2.2.9-2+deb11u3"

declare -a nameserver_ip=("master-1 $IP_MASTER_1" "master-2 $IP_MASTER_2" "master-3 $IP_MASTER_3")

echo -e "Install haproxy\n"
apt-get update && apt-get install -y haproxy=$VERSION

echo -e "Starting and enable service haproxy\n"
systemctl start haproxy
systemctl enable haproxy

echo -e "\nConfigure haproxy\n"
cat <<EOF > /etc/haproxy/haproxy.cfg
#---------------------------------------------------------------------
# Global settings
#---------------------------------------------------------------------
global
    log         127.0.0.1 local2     #Log configuration

    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     8000
    user        haproxy             #Haproxy running under user and group "haproxy"
    group       haproxy
    daemon

    # turn on stats unix socket
    stats socket /var/lib/haproxy/stats

#---------------------------------------------------------------------
# common defaults that all the 'listen' and 'backend' sections will
# use if not designated in their block
#---------------------------------------------------------------------
defaults
    mode                    http
    log                     global
    # option                  httplog
    option                  dontlognull
    option http-server-close
    option forwardfor       except 127.0.0.0/8
    option                  redispatch
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         10s
    timeout client          1m
    timeout server          1m
    timeout http-keep-alive 10s
    timeout check           10s
    maxconn                 3000

#---------------------------------------------------------------------
#HAProxy Monitoring Config
#---------------------------------------------------------------------

listen stats
bind *:8080
        mode http
        option forwardfor
        option httpclose
        stats enable
        stats show-legends
        stats refresh 5s
        stats uri /stats
        stats realm Haproxy\ Statistics
        stats auth loadbalancer:loadbalancer
        stats admin if TRUE

#---------------------------------------------------------------------
# FrontEnd Configuration
#---------------------------------------------------------------------

frontend front_kubernetes
        bind  *:6443
        mode tcp
        default_backend back_kubernetes

#---------------------------------------------------------------------
# BackEnd roundrobin as balance algorithm
#---------------------------------------------------------------------

backend back_kubernetes
    mode tcp
    balance roundrobin                                   #Balance algorithm
EOF

for data in "${nameserver_ip[@]}"
do
  echo "    server $data:6443 check" >> /etc/haproxy/haproxy.cfg
done

echo -e "\nRestart service keepalived\n"
systemctl restart haproxy

echo "Finish install"