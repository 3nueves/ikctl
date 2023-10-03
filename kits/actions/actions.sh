#!/bin/bash

show(){
    df -hT | grep "/dev"
}

clean(){
    echo -e "Cleaning logs\n"

    journalctl --vacuum-size=100M
    /usr/sbin/logrotate -f /etc/logrotate.d/syslog --state /etc/logrotate.status
    /usr/sbin/logrotate -f /etc/logrotate.d/daemon --state /etc/logrotate.status
    
    cd /var/log
    > syslog
    > syslog.1
    > daemon.log
    > daemon.log.1

    show

    echo -e "\nLogs clean"
} 

hola(){
    echo -e "Hola mundo"
}

k_nodes(){
    kubectl get nodes -o wide
}

check(){
    ls -a
    pwd
}

$1