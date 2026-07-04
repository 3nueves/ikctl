#!/bin/bash
# v1.0 by David Moya to invisible bits
# Install Keepalived + vrrp

echo -e "Starting installation\n"

echo -e "Set variables\n"

export IP=$1
export VERSION="1:2.1.5-0.2+deb11u1"
export INTERFACE=$(ifconfig | grep ${IP} -B 1 | awk '{print $1}'|head -n 1|cut -d ':' -f -1)
export IPV="10.60.0.100"
export PRIORITY="101"

echo -e "Config sysctl for keepalived\n" 

cat <<EOF > /etc/sysctl.d/keepalived.conf
#Allow binding to VRRP floating IP
net.ipv4.ip_nonlocal_bind=1
net.ipv4.ip_forward = 1
EOF

sysctl -p

echo -e "Install keepalived and killall\n"

apt update && apt install -y psmisc keepalived=$VERSION


echo -e "\nConfig keepalived\n"

cat <<EOF > /etc/keepalived/keepalived.conf
vrrp_script chk_haproxy {
  script "/usr/bin/killall -0 haproxy"
  interval 2
  weight 2
}

vrrp_instance VI_1 {
  interface $INTERFACE
  state MASTER
  virtual_router_id 1
  priority $PRIORITY
  virtual_ipaddress {
    $IPV
  }
  track_script {
    chk_haproxy
  }
  authentication {
    auth_type PASS
    auth_pass ZcnG9lGUoZeM3nFT
    }
}
EOF

echo -e "\nRestart service keepalived\n"

systemctl restart keepalived

echo "Finish install"