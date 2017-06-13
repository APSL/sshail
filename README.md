# Overview

This projects try to simplify the way you do a SSH jail to limit
the resources (software / files) that SSH users can access on a server.

A `sshail` is a docker container running SSH inside and some directories
mounted in order to limit the software and visiblilty of the user inside
the container, just like an SSH jail but easier to configure.

Also you can have virtual users only aviable in the sshail mapped to
real users outside the container so you can manipulate the files
and permissions easy.

The sshails are destroyed daily for security and avoid resouce exhaustion.

# Usage example

The user requests a sshail to `server1.example.com`:

    curl https://myuser@server1.example.com:1934/ssh

It will respond with something like:

    ssh myuser@server1.example.com -p 12200 # Valid until yyyy-mm-dd hh:mm:ss


# Install & configure

First of all you will need `docker` installer properly on your system. Visit
the official documentation to do that.

On Debian based systems you can install the `debrequirements.txt` with `apt` if you
want to avoid installing them with pip3.

    apt install $(curl https://raw.githubusercontent.com/APSL/sshail/master/debrequirements.txt | sed ':a;N;$!ba;s/\n/ /g')

Of course you can alse make a virtualenv and install `requeriments.txt`

Then install sshail:

    pip3 install -U git+https://github.com/APSL/sshail.git

Configure (if you want to do it automagically):

    sshail --deploy # As Root

This script will:
    - Create the /etc/sshail directory for configurations
    - Add a user on the system called `sshail` with permissions to manage Docker
    - Deploy a systemd configuration to start sshail with `service sshail start`
    - Deploy a cron to kill periodically the sshails

If `sshail --deploy` does not meet your system you can do it by hand.

## /etc/sshail/conf.ini

The main SSHail configuration file for general application settings.

| Setting                   | Description                                         |
|---------------------------|-----------------------------------------------------|
| `SSHAIL_PORT`             | Port to listen the sshail HTTP API                  |
| `SSHAIL_SSH_HOST`         | Hostname to give to the users to do the SSH command |
| `SSHAIL_DAILY_PURGE_TIME` | Which hour should the sshails be purged             |
| `SSHAIL_PORT_RANGE`       | Port range for the SSH to reach the sshails         |


### Basic Example

    SSHAIL_PORT=1958
    SSHAIL_SSH_HOST="127.0.0.1"
    SSHAIL_DAILY_PURGE_TIME="04:00"
    SSHAIL_PORT_RANGE="12200-12299"


## /etc/sshail/sshails.yml

At this file you can specify a list of the enabled sshails.

| Field          | Description                                                    |
|----------------|----------------------------------------------------------------|
| `user`         | Virutal SSH user for the container and the HTTP API            |
| `real_user`    | Real user of the host system to inherit permissions            |
| `basic_passwd` | Password (clear text) for the HTTP API basic auth              |
| `user_crypt`   | Linux crypt for `/etc/shadow` for the `user` inside the sshail |

### Basic Example

    sshails:
        -
            user: mike
            real_user: test1
            basic_passwd: "123"
            user_crypt: '$6$aOoiKGBC$Ap1U9EFSmgPqZRgrbwbvQEqFjqGlTJ5OOJ5WvVxw7WYXhDzukUETlCvyo0iPkFzIHWgNKfQ227VuBcyyyyyyyy'
        -
            user: bob
            real_user: test2
            basic_passwd: "456"
            user_crypt: '$6$aOoiKkBC$Ap1U9EFSmgPqZRgrbwbvQEqFjqGlTJ5OOJ5WvVxw7WYXhDzukUETlCvyo0iPkFzIHWgNKfQ227VuBcwzzzzzzz'
