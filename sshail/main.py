#!/usr/bin/env python3

import os
import logging

from sys import exit, stdout
from datetime import datetime

import yaml
import click
import docker

from dateutil import relativedelta
from flask import Flask, request, redirect

from sshail import sshails
from sshail.sshail import Sshail, purge_sshails, build_image
from sshail.deploy import deploy_conf
from sshail.addsshail import addsshail as sshailadd
from sshail.basic_auth import basic_auth


app = Flask(__name__)

CONF_DIR = "/etc/sshail"
DEFAULT_IMAGE= 'sshail-minimal'

if __name__ == "__main__":
    sshail()


@click.command()
@click.option("--deploy", is_flag=True, help="Deploy sshail configuration")
@click.option("--purge", is_flag=True, help="Purge expired sshails")
@click.option("--build-docker-image", is_flag=True, help="Force rebuild for docker image")
@click.option("--addsshail", help="Generate a user sshail")
def sshail(deploy, addsshail, build_docker_image, purge):

    log = logging.getLogger(__name__)

    if stdout.isatty():
        log_handler = logging.StreamHandler(stdout)
        log_handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        log_handler = logging.FileHandler('/var/log/sshail.log')
        log_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))

    log_handler.setLevel(logging.INFO)
    log.addHandler(log_handler)
    log.setLevel(logging.INFO)

    error = False

    if deploy:
        error = deploy_conf(log=log)
        exit(error)

    if purge:
        try:
            error = purge_sshails(log=log)

        except Exception as exc:
            if log:
                log.error(exc)

        exit(error)

    if build_docker_image:
        build_image(docker.from_env(), log, DEFAULT_IMAGE)

    if addsshail:
        error = sshailadd(user=addsshail, log=log)
        exit(error)

    api_http(log_handler=log_handler)


def api_http(log_handler=None):
    app.config.from_pyfile(os.path.join(CONF_DIR, 'conf.ini'))
    app.docker = docker.from_env()

    with open(os.path.join(CONF_DIR, 'sshails.yml'), 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as exc:
            # TODO
            raise exc

    sshails.data = [x for x in config['sshails']] if config else []

    if log_handler:
        app.logger.addHandler(log_handler)

    app.run(host='0.0.0.0', port=app.config['SSHAIL_PORT'])


@app.route('/')
def index():
    return redirect("/ssh", code=302)


@app.route('/ssh')
@basic_auth
def ssh_view():
    username = request.authorization.username

    daily_purge_time = app.config['SSHAIL_DAILY_PURGE_TIME']

    user = sshails.user_data(username)

    image = user.get('image', DEFAULT_IMAGE)
    real_user = user['real_user']
    virt_crypt = user['user_crypt']
    virt_home = user.get('virt_home', '/home/{}'.format(username))


    if 'ttl' in user:
        ttl = user['ttl']
        # TODO some func here to parse other values
        if ttl.endswith('h'):
            hours = int(ttl.replace('h', ''))

        expire_date = datetime.now() + relativedelta.relativedelta(hours=hours)
    else:
        expire_h = int(daily_purge_time.split(':')[0])
        expire_m = int(daily_purge_time.split(':')[1])
        expire_date = datetime.now() + relativedelta.relativedelta(
            days=1,
            hour=expire_h,
            minute=expire_m,
        )

    sshail = Sshail(
        image=image,
        real_user=real_user,
        virt_user=username,
        virt_crypt=virt_crypt,
        virt_home=virt_home,
        ssh_host=app.config['SSHAIL_SSH_HOST'],
        expire_date=expire_date,
        ssh_port_range=app.config['SSHAIL_PORT_RANGE'],
        log=app.logger,
    )

    if sshail.status != 'running':
        print("Sshail is not running, starting it")
        sshail.start()

    ssh_command = "ssh {user}@{host} -p {port} # Exipres at {date}".format(
        user=sshail.username,
        host=sshail.ssh_host,
        port=sshail.ssh_port,
        date=sshail.expire_date.strftime("%Y-%m-%d %H:%M"),
    )

    msg = "Giving access to {} at {} port {}"
    app.logger.info(msg.format(sshail.username, sshail.ssh_host, sshail.ssh_port))

    return (ssh_command)
