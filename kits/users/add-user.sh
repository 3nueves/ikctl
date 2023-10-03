#!/bin/bash
# invisiblebits.com
# v1.0 by David Moya

echo -e "Create user kub\n"
adduser --home /home/kub --shell /bin/bash --uid 1001 --disabled-password --gecos GECOS kub

echo -e "Change password\n"
echo -en "changeme01\nchangeme01\nchangeme01\n" | passwd kub

echo -e "Enable access from ssh keys\n"
mkdir -p /home/kub/.ssh/
touch /home/kub/.ssh/authorized_keys
cat $HOME/.ikctl/id_rsa_kubernetes.pub >> /home/kub/.ssh/authorized_keys
chmod 700 /home/kub/.ssh
chmod 600 /home/kub/.ssh/authorized_keys
chown 1000.1000 /home/kub -R

echo -e "Add nopasswd in sodoers group\n"
echo 'kub ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers.d/kub
chmod 440 /etc/sudoers.d/kub
usermod -aG sudo kub

echo -e "Change keywoard to ES\n"
sed -i "s/pc105/pc104/g" /etc/default/keyboard
sed -i "s/gb/es/g" /etc/default/keyboard