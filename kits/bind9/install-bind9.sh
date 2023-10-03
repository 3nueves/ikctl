#!/bin/bash
# v1.0 by David Moya to invisible bits
# Install bind9

echo -e "Starting installation\n"

echo -e "Set variables\n"

export VERSION="1:9.16.37-1~deb11u1"
export NAMESERVER=$1
export IP1="10.100.0.53"
export IP2="10.100.0.54"
export NETWORK="10.100.0.0/24"
export SHORT_NET="10.100.0"
export SEARCH=""
export DNS="false"
export ZONE="test.test.lan"
export REVERSE_ZONE="0.60.10.in-addr.arpa"
export HOSTNAME=$(hostname)

echo -e "Install bind9\n"
apt-get update && apt-get install -y bind9=$VERSION bind9utils=$VERSION bind9-doc=$VERSION dnsutils=$VERSION

echo -e "Starting and enable service bind9\n"
systemctl enable bind9
systemctl start bind9

echo -e "\nCreate directories and permisions\n"
mkdir -p /var/cache/bind/dynamic /var/cache/bind/data /var/cache/bind/secondary
chmod 770 /var/cache/bind/dynamic /var/cache/bind/data /var/cache/bind/secondary -R

echo -e "\nConfigure bind9\n"

if [ ${NAMESERVER}==${HOSTNAME} ];then

cat <<EOF > /etc/bind/named.conf
//
// named.conf
//
acl "acl1" {
  ${NETWORK};
};

options {
  listen-on port 53 { any; };
  listen-on-v6 port 53 { ::1; };
  directory   "/var/cache/bind";
  dump-file   "/var/cache/bind/data/cache_dump.db";
  statistics-file "/var/cache/bind/data/named_stats.txt";
  memstatistics-file "/var/cache/bind/data/named_mem_stats.txt";
  allow-query     { any; };
  allow-transfer  { "acl1"; };
  check-names  master ignore;

  recursion yes;
  allow-recursion { any; };
  forwarders { 8.8.8.8; 8.8.4.4; };  
  rrset-order { order random; };

  /* Path to ISC DLV key */
  bindkeys-file "/etc/named.iscdlv.key";

  managed-keys-directory "/var/cache/bind/dynamic";

  pid-file "/run/named/named.pid";
  session-keyfile "/run/named/session.key";

  querylog yes;
  dns64 64:ff9b::/96 {
    clients { any;  };
  };
};

statistics-channels {
  inet ${IP1} port 8053 allow { any; };
};

logging {
  channel default_debug {
    file "data/named.run";
    severity dynamic;
    print-time yes;
  };
  channel querylog {
          file "data/query.log" versions 600 size 20m;
        severity dynamic;
    print-time yes;
  };
  category queries { querylog; };
};

include "/etc/bind/named.conf.default-zones";

zone "${ZONE}" IN {
  type master;
  file "/var/cache/bind/${ZONE}";
  notify yes;
  allow-update { none; };
};

zone "${REVERSE_ZONE}" IN {
  type master;
  file "/var/cache/bind/${REVERSE_ZONE}";
  notify yes;
  allow-update { none; };
};
EOF

echo -e "Add register file"

cat <<EOF > /var/cache/bind/${ZONE}
; Hash: dd996f992fd9bc1bc43153ad15f4d419 1630923106
; Zone file for ${ZONE}
;
; cloud-init created
;

\$ORIGIN ${ZONE}.
\$TTL 2W

@ IN SOA dns-1.${ZONE}. admin.${ZONE}. (
  1646905590
  2D
  2H
  2W
  2D )

                           IN  NS     dns-1.${ZONE}.
                           IN  NS     dns-2.${ZONE}.

dns-1                      IN  A      ${IP1}
dns-2                      IN  A      ${IP2} 
manager-1                  IN  A      ${IP1}
manager-2                  IN  A      ${IP2} 
karma                      IN  A      ${SHORT_NET}.9
argocd                     IN  A      ${SHORT_NET}.9
alertmanager               IN  A      ${SHORT_NET}.9
grafana                    IN  A      ${SHORT_NET}.9
prometheus                 IN  A      ${SHORT_NET}.9
rabbitmq                   IN  A      ${SHORT_NET}.9
minio                      IN  A      ${SHORT_NET}.9
investigator               IN  A      ${SHORT_NET}.9
delfos-forum               IN  A      ${SHORT_NET}.9
haproxy-1                  IN  A      ${SHORT_NET}.21
haproxy-2                  IN  A      ${SHORT_NET}.22
collectors                 IN  A      ${SHORT_NET}.23
forum-coordinator          IN  A      ${SHORT_NET}.24
mariadb                    IN  A      ${SHORT_NET}.25
endpoint-kubes             IN  A      ${SHORT_NET}.100
k8s                        IN  A      ${SHORT_NET}.100
master-1                   IN  A      ${SHORT_NET}.1
master-2                   IN  A      ${SHORT_NET}.4
master-3                   IN  A      ${SHORT_NET}.3
worker-1                   IN  A      ${SHORT_NET}.11
worker-2                   IN  A      ${SHORT_NET}.12
worker-3                   IN  A      ${SHORT_NET}.13
worker-4                   IN  A      ${SHORT_NET}.14
worker-5                   IN  A      ${SHORT_NET}.15
worker-6                   IN  A      ${SHORT_NET}.16
EOF

cat <<EOF > /var/cache/bind/${REVERSE_ZONE}
; Hash: 6538b0a0961e311704bf2b6cf38b18aa 1630923106
; Reverse zone file for ${ZONE}
;
; cloud-init created
;

\$TTL 2W
\$ORIGIN ${REVERSE_ZONE}.

@ IN SOA dns-1.${ZONE}. admin.${ZONE}. (
  1646905590
  2D
  2H
  2W
  2D )

                       IN  NS   dns-1.${ZONE}.
                       IN  NS   dns-2.${ZONE}.

53                     IN  PTR  dns-1.${ZONE}.
54                     IN  PTR  dns-2.${ZONE}.
53                     IN  PTR  manager-1.${ZONE}.
54                     IN  PTR  manager-2.${ZONE}.
9                      IN  PTR  karma.${ZONE}.
9                      IN  PTR  argocd.${ZONE}.
9                      IN  PTR  alertmanager.${ZONE}.
9                      IN  PTR  grafana.${ZONE}.
9                      IN  PTR  prometheus.${ZONE}.
9                      IN  PTR  rabbitmq.${ZONE}.
9                      IN  PTR  minio.${ZONE}.
9                      IN  PTR  investigator.${ZONE}.
9                      IN  PTR  delfos-forum.${ZONE}.
24                     IN  PTR  forum-coordinator.${ZONE}.
23                     IN  PTR  collectors.${ZONE}.
25                     IN  PTR  mariadb.${ZONE}.
21                     IN  PTR haproxy-1.${ZONE}.
22                     IN  PTR haproxy-2.${ZONE}.
100                    IN  PTR  endpoint-kubes.${ZONE}.
100                    IN  PTR  k8s.${ZONE}.
1                      IN  PTR  master-1.${ZONE}.
4                      IN  PTR  master-2.${ZONE}.
3                      IN  PTR  master-3.${ZONE}.
11                     IN  PTR  worker-1.${ZONE}.
12                     IN  PTR  worker-2.${ZONE}.
13                     IN  PTR  worker-3.${ZONE}.
14                     IN  PTR  worker-4.${ZONE}.
15                     IN  PTR  worker-5.${ZONE}.
16                     IN  PTR  worker-6.${ZONE}.
EOF

elif [ ${NAMESERVER}==${HOSTNAME} ]; then

cat <<EOF > /etc/bind/named.conf
//
// named.conf
//
//
acl "acl1" {
  ${NETWORK};
};

options {
  listen-on port 53 { any; };
  listen-on-v6 port 53 { ::1; };
  directory   "/var/cache/bind";
  dump-file   "/var/cache/bind/data/cache_dump.db";
  statistics-file "/var/cache/bind/data/named_stats.txt";
  memstatistics-file "/var/cache/bind/data/named_mem_stats.txt";
  allow-query     { any; };
  allow-transfer  { "acl1"; };
  check-names  master ignore;

  recursion yes;
  allow-recursion { any; };
  forwarders { 8.8.8.8; 8.8.4.4; };  
  rrset-order { order random; };

  /* Path to ISC DLV key */
  bindkeys-file "/etc/named.iscdlv.key";

  managed-keys-directory "/var/cache/bind/dynamic";

  pid-file "/run/named/named.pid";
  session-keyfile "/run/named/session.key";

  querylog yes;
  dns64 64:ff9b::/96 {
    clients { any;  };
  };
};

statistics-channels {
  inet ${IP2} port 8053 allow { any; };
};

logging {
  channel default_debug {
    file "data/named.run";
    severity dynamic;
    print-time yes;
  };
  channel querylog {
          file "data/query.log" versions 600 size 20m;
        severity dynamic;
    print-time yes;
  };
  category queries { querylog; };
};

include "/etc/bind/named.conf.default-zones";

zone "${ZONE}" IN {
  type slave;
  masters { ${IP1}; };
  file "/var/cache/bind/secondary/${ZONE}";
};

zone "${REVERSE_ZONE}" IN {
  type slave;
  masters { ${IP2}; };
  file "/var/cache/bind/secondary/${REVERSE_ZONE}";
};
EOF

else

echo -e "\nNo server was installed\n"

fi

echo -e "\nChange owner"
chown root.bind /var/cache/bind -R
systemctl restart bind9

echo "Finish install"