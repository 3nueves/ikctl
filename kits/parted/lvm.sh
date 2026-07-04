#!/bin/bash

lvm(){

for part in ${parts[@]}
do
echo $part
pvcreate $part
vgcreate $vg $part  
lvcreate -l 100%FREE -n $lv $vg
mkfs.ext4 /dev/mapper/vg--hot--7-lv--hot--7 && \

cat >> /etc/fstab <<EOF
# elastic partitions
/dev/mapper/vg--hot--7-lv--hot--7   /opt/hot-7      ext4    defaults        0       2
EOF
mkdir -p $path 
mount -a
done

}