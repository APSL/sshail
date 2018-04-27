#!/bin/bash

set -e

# sshail entrypoint, repare the user home
# and starts the ssh daemon

## Envirnment variables that are used ##
user="$SSHAILENV_USER"
home="$SSHAILENV_USER_HOME"
crypt="$SSHAILENV_USER_CRYPT"
uid="$SSHAILENV_USER_UID"
gid="$SSHAILENV_USER_GID"

if [ -z "$user" ]
then
    echo "Missing SSHAILENV_USER"
    exit 1
fi

if [ -z "$home" ]
then
    echo "Missing SSHAILENV_USER_HOME"
    exit 1
fi

if [ -z "$crypt" ]
then
    echo "Missing SSHAILENV_USER_CRYPT"
    exit 1
fi

if [ -z "$uid" ]
then
    echo "Missing SSHAILENV_USER_UID"
    exit 1
fi


if [ -z "$gid" ]
then
    echo "Missing SSHAILENV_USER_GID"
    exit 1
fi


group=$(echo "$user" | cut -b -16)

getent group "$group" || \
    groupadd -g $gid "$group"

id -u "$user" &>/dev/null || \
    useradd -u $uid -g $gid -m --home-dir "$home" -p "$crypt" -s /bin/bash "$user"

mkdir -p /var/run/sshd
chmod 0755 /var/run/sshd

mkdir -p /provisioned/

# Directory for other images to extend entrypoint funcionality
while read -r file
do
    [ "$file" == "." ] && continue
    [ "$file" == ".." ] && continue
    if [ ! -e /provisioned/"$file" ];
    then
        echo "Provisioning $file"
        /entrypoint.d/"$file"
        touch /provisioned/"$file"
    else
        echo "$file already provisioned, skipping"
    fi

done < <(ls -f /entrypoint.d)

echo "Starting SSH"
/usr/sbin/sshd -D
echo "SSH is dead, exiting"
