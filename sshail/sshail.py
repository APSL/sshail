"""
" Module to abstract docker into sshails
"""

from pwd import getpwnam
from datetime import datetime
from contextlib import closing

from socket import socket, AF_INET, SOCK_STREAM

import docker
import dateutil.parser

def purge_sshails(prefix='sshail', delim='-', log=None):
    """
    " Look for sshails that has been expired and stop and remove them.
    " @return True if some error else otherwise
    """

    error = False
    dock = docker.client.from_env()

    for container in dock.containers.list():
        sshail_fields = parse_container_name(
                            container.name,
                            prefix=prefix,
                            delim=delim,
                        )
        if sshail_fields:
            now = datetime.now().strftime("%Y%m%d%H%M")

            if sshail_fields['date'] < now:
                if log:
                    msg = "Purge: {} has expired, purging it!"
                    log.info(msg.format(container.name))

                    container.stop()
                    try:
                        container.remove()

                    except docker.errors.NotFound:
                        # Ingore if container already had --rm
                        pass

                    except docker.errors.APIError:
                        container.kill()
                        container.remove()

            else:
                if log:
                    msg = "Purge: {} seem to be a sshail but isn't expired yet."
                    log.info(msg.format(container.name))
        else:
            if log:
                msg = "Purge: {} not considered a sshail, skipping"
                log.info(msg.format(container.name))

    return error


def parse_container_name(name, prefix="sshail", delim="-"):
    from re import match

    cn_regex = r"^{prefix}{delim}(?P<username>.*){delim}(?P<date>\d+)$".format(
        prefix=prefix,
        delim=delim,
    )

    valid_name = match(cn_regex, name)
    if valid_name:
        return valid_name.groupdict()
    else:
        return {}


class Sshail(object):
    """
    " Define a sshail which is a docker container
    " containing an ssh process mapping real_users into
    " virtual_users
    """

    def __init__(self,
                 image="sshail-minimal",
                 real_user=None,
                 virt_user=None,
                 virt_crypt=None,
                 virt_home=None,
                 ssh_host='localhost',
                 expire_date=None,
                 ports={},
                 volumes={},
                 ssh_port_range=None,
                 log=None,
                ):
        # Given attributes
        self.__image = image
        self.__real_user = real_user
        self.__virt_user = virt_user
        self.__virt_crypt = virt_crypt
        self.__virt_home = virt_home or "/home/{}".format(self.virtual_user)
        self.__ssh_host = ssh_host
        self.__expire_date = expire_date
        self.__ports = ports
        self.__volumes = volumes
        self.__ssh_port_range = ssh_port_range
        self.__log = log

        # Generated attributes
        self.__real_home = getpwnam(self.real_user).pw_dir

        home_volume = {
            self.__real_home: {"bind": self.__virt_home, "mode": "rw"}
        }
        self.__volumes.update(home_volume)

        self.__env = [
            "SSHAILENV_USER={}".format(self.virtual_user),
            "SSHAILENV_USER_UID={}".format(getpwnam(self.real_user).pw_uid),
            "SSHAILENV_USER_GID={}".format(getpwnam(self.real_user).pw_gid),
            "SSHAILENV_USER_HOME={}".format(self.__virt_home),
            "SSHAILENV_USER_CRYPT={}".format(self.__virt_crypt),
        ]
        self.__docker = docker.client.from_env()

        self.__ssh_port = None
        self.__container = None

        self.associate_matching_container()


    def associate_matching_container(self):
        """
        " Associate this sshail to the mathcing container if running
        " @return True if Sshail was still running or False otherwise
        """
        for container in self.__docker.containers.list(all=True):
            #container_name_data = parse_container_name(container.name)
            if container.name == self.name:
                if container.status == 'running':
                    self.__ssh_port = container.attrs['HostConfig']['PortBindings']['22/tcp'][0]['HostPort']
                    self.__container = container
                    if self.__log:
                        msg = "Assotiating sshail to running container {}"
                        self.__log.info(msg.format(self.name))
                    return True
                else:
                    container.remove()
                    return False

        return False


    def start(self):
        """
        " Starts the docker container associated to this sshail
        """

        if self.status == 'running':
            return

        self.__ssh_port = self.get_free_port()
        ssh_port = {
            "22/tcp": self.ssh_port
        }
        self.__ports.update(ssh_port)

        try:
            if self.__log:
                msg = "Going to start {}"
                self.__log.info(msg.format(self.name))

            self.__container = self.__docker.containers.run(
                self.__image,
                name=self.name,
                ports=self.__ports,
                volumes=self.__volumes,
                environment=self.__env,
                detach=True,
            )
        except docker.errors.ImageNotFound:
            if self.__log:
                msg = "Building image {}"
                self.__log.info(msg.format(self.__image))

            image_path = "/etc/sshail/images/{}".format(self.__image)
            self.__docker.images.build(path=image_path, tag=self.__image)

            self.__container = self.__docker.containers.run(
                self.__image,
                name=self.name,
                ports=self.__ports,
                volumes=self.__volumes,
                environment=self.__env,
                detach=True,
            )

        if self.__log:
            msg = "The sshail {} has been started"
            self.__log.info(msg.format(self.name))


    def stop(self):
        """
        " Stops the docker container associated to this sshail
        """
        if self.__log:
            msg = "Stopping {}"
            self.__log.info(msg.format(self.name))

        self.__container.stop()


    def destory(self):
        """
        " Destroy the docker container associated to this sshail
        """
        if self.__log:
            msg = "Destroying {}"
            self.__log.info(msg.format(self.name))

        self.__container.remove()


    @property
    def status(self):
        return self.__container.status if self.__container else None


    @property
    def username(self):
        return self.virtual_user or self.real_user


    @property
    def real_user(self):
        return self.__real_user


    @property
    def virtual_user(self):
        return self.__virt_user


    @property
    def ssh_port(self):
        return self.__ssh_port


    @property
    def ssh_host(self):
        return self.__ssh_host


    @property
    def start_date(self):
        if self.__container:
            return dateutil.parser.parse(
                self.__container.attrs['State']['StartedAt'],
            )
        return None


    @property
    def expire_date(self):
        return self.__expire_date


    @property
    def name(self, prefix="sshail", delim="-"):
        return "{prefix}{delim}{user}{delim}{date}".format(
            prefix=prefix,
            delim=delim,
            user=self.__virt_user or self.__real_user,
            date=self.__expire_date.strftime("%Y%m%d%H%M"),
        )


    def get_free_port(self, port_range=None):
        if not port_range:
            port_range = self.__ssh_port_range

        port_start = int(port_range.split('-')[0])
        port_end = int(port_range.split('-')[1])

        for port in range(port_start, port_end + 1):
            try:
                with closing(socket(AF_INET, SOCK_STREAM)) as sock:
                    sock.bind(('', port))
            except OSError:
                # Skip this port and try another one
                continue

            if self.__log:
                self.__log.info("Port {} seem to be free".format(port))
            return port

        return None
