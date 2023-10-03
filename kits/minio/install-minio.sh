#!/bin/bash

echo -e "## Starting ----------------------------------------\n"

apt-get update && apt-get install -y sudo vim net-tools curl

echo -e "## Change keyboard----------------------------------\n"

sed -i "s/pc105/pc104/g" /etc/default/keyboard
sed -i "s/gb/es/g" /etc/default/keyboard


echo -e "## Add ssh key------------------------------------------\n"

mkdir -p /home/minio-user/.ssh/
touch /home/minio-user/.ssh/authorized_keys
cat $HOME/ikctl/id_rsa_kubernetes-unelink.pub >> /home/minio-user/.ssh/authorized_keys
chown minio-user. /home/minio-user/.ssh -R

echo "## add sudores"
cat > /etc/sudoers.d/minio-user <<EOF
minio-user ALL=(ALL:ALL) NOPASSWD: ALL
EOF

/usr/sbin/sysctl --system

echo -e "## Install Minio---------------------------------------------------------\n"

wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
cp minio /usr/local/bin

cat <<EOT >> /etc/default/minio
# Remote volumes to be used for MinIO server.
MINIO_VOLUMES=/opt/minio/disk{1...12}
# Use if you want to run MinIO on a custom port.
MINIO_OPTS="--address :9000 --console-address :39000"
# Root user for the server.
MINIO_ROOT_USER=minio
# Root secret for the server.
MINIO_ROOT_PASSWORD=yVyI54Lh9QgH
#Storage Class
MINIO_STORAGE_CLASS_STANDARD=EC:3
#MINIO_STORAGE_CLASS_RSS=EC:2
# Allow metrics for prometheus
MINIO_PROMETHEUS_AUTH_TYPE="public"
EOT

( cd /etc/systemd/system/; curl -O https://raw.githubusercontent.com/minio/minio-service/master/linux-systemd/minio.service )

systemctl enable minio.service

chown minio-user. /opt/minio/ -R

echo -e "## Finish Install----------------------------------------------------------------\n"