#!/bin/bash

declare -a parts=($@)

create(){

for part in ${parts[@]}
do
if [[ $part =~ ^/dev/.*$ ]];then
echo $part
cat <<EOF | tee parted.sfdisk
    label: gpt
    device: $part
    unit: sectors
    ${part} : start=2048, type=31
EOF
cat parted.sfdisk
sfdisk $part < parted.sfdisk
fi
done
}

if [ $1 == "help" ];then
    echo "ikctl -i parted -n <name-kit> -s sudo -p 'create /dev/sda /dev/sdb /dev/sdc /dev/sdd'"
else
    $1
fi
