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

groupadd -g $gid "$group"
useradd -u $uid -g $gid -m --home-dir "$home" -p "$crypt" -s /bin/bash "$user"

mkdir /var/run/sshd
chmod 0755 /var/run/sshd

# Directory for other images to extend entrypoint funcionality
while read -r file
do
    [ "$file" == "." ] && continue
    [ "$file" == ".." ] && continue
    /entrypoint.d/"$file"

done < <(ls -f /entrypoint.d)

/usr/sbin/sshd -D

