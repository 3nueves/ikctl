#!/bin/bash

# Variables
export PARTNER=aiuken
export CUSTOMER=dia-brasil

echo -e "Install telegraf\n"

wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
source /etc/os-release
test $ID = "ubuntu" && echo "deb https://repos.influxdata.com/ubuntu $VERSION_CODENAME stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
test $ID = "debian" && echo "deb https://repos.influxdata.com/debian $VERSION_CODENAME stable" | sudo tee /etc/apt/sources.list.d/influxdb.list

apt update && apt install telegraf

echo """
[agent]
  hostname = \"$PARTNER-$CUSTOMER-forwarder\"
  flush_interval = \"15s\"
  interval = \"15s\"
  logfile = \"/var/log/telegraf/telegraf.log\"
[[inputs.cpu]]
[[inputs.mem]]
[[inputs.system]]
[[inputs.disk]]
  mount_points = [\"/\"]
[[inputs.processes]]
[[inputs.net]]
  fieldpass = [ \"bytes_*\" ]
# InfluxDB server config
[[outputs.influxdb]]
  database = \"telegraf\"
  urls = [ \"https://monitor.invisiblebits.com:80\" ]
  insecure_skip_verify = true
""" >/etc/telegraf/telegraf.conf

systemctl enable telegraf && systemctl restart telegraf