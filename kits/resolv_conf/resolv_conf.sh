#!/bin/bash
# v1.0 by David Moya to invisible bits
# Config resolv.conf

echo -e "Config resolf.conf\n"

echo -e "Set variables\n"

export NAMESERVER1="10.77.110.1"
export NAMESERVER2="10.77.110.2"
export SEARCH="topnet.ibits.lan"
export DNS="false"

echo -e "Change resolv.conf\n" 

if [ "$DNS" = true ]; then
cat <<EOF > /etc/resolv.conf
nameserver 127.0.0.1
search $SEARCH
EOF
else
cat <<EOF > /etc/resolv.conf
search $SEARCH
nameserver $NAMESERVER1
nameserver $NAMESERVER2
EOF
fi

echo "Finish install"