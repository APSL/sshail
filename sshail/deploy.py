import os
import shlex
import shutil

from pwd import getpwnam
from grp import getgrnam

from subprocess import check_call, CalledProcessError


def deploy_file(src, dst, log=None):
    error = False

    if not os.path.exists(dst):
        if log:
            msg = "Deploying {} to {}"
            log.info(msg.format(src, dst))

        try:
            shutil.copy(src, os.path.dirname(dst))
        except PermissionError as exc:
            error = True
            log.error(exc)
    else:
        if log:
            msg = "File {} already exist, skipping."
            log.info(msg.format(dst))

    return error


def copy_files(log=None):
    deploy_filename = os.path.realpath(__file__)
    sshail_dir = os.path.dirname(deploy_filename)
    conf_dir = os.path.join(sshail_dir, "conf")

    error = False

    systemd_src = os.path.join(conf_dir, "lib/systemd/system/sshail.service")
    systemd_dst = "/lib/systemd/system/sshail.service"
    error |= deploy_file(systemd_src, systemd_dst, log=log)

    cron_src = os.path.join(conf_dir, "etc/cron.d/sshail")
    cron_dst = "/etc/cron.d/sshail"
    error |= deploy_file(cron_src, cron_dst, log=log)

    etc_src = os.path.join(conf_dir, "etc/sshail")
    etc_dst = "/etc/sshail"
    if not os.path.exists(etc_dst):
        if log:
            msg = "Deploying {} to {}"
            log.info(msg.format(systemd_src, systemd_dst))

        try:
            shutil.copytree(etc_src, etc_dst)
        except PermissionError as exc:
            error = True
            log.error(exc)
    else:
        if log:
            msg = "File {} already exist, skipping."
            log.info(msg.format(etc_dst))

    return error


def add_sshail_user(log=None):
    user = "sshail"
    uid = 12199
    gid = uid
    home = "/var/lib/sshail"

    groups = "docker"

    error = False

    group_add_tpl = (
        'groupadd '
        '--gid {gid} '
        '--system '
        '{group}'
    )

    group_add_cmd = group_add_tpl.format(
        gid=gid,
        group=user,
    )

    try:
        getgrnam(user)
        if log:
            msg = "Group {} already exist, skipping."
            log.info(msg.format(user))
    except KeyError:
        if log:
            msg = "Group {} does not exist creating it."
            log.info(msg.format(user))

        try:
            check_call(shlex.split(group_add_cmd))
        except CalledProcessError as exc:
            error = True
            log.error(exc)

    user_add_tpl = (
        'useradd '
        '--home-dir {home} '
        '--uid {uid} '
        '--gid {gid} '
        '--groups {groups} '
        '--system '
        '{user}'
    )

    user_add_cmd = user_add_tpl.format(
        home=home,
        uid=uid,
        gid=gid,
        groups=groups,
        user=user,
    )

    try:
        getpwnam(user)
        if log:
            msg = "User {} already exist, skipping."
            log.info(msg.format(user))
    except KeyError:
        if log:
            msg = "User {} does not exist creating it."
            log.info(msg.format(user))
        try:
            check_call(shlex.split(user_add_cmd))
        except CalledProcessError as exc:
            error = True
            log.error(exc)

    return error


def deploy_conf(log=None):
    if log:
        log.info("Starting SSHail deploy")

    error = False

    error |= add_sshail_user(log=log)
    error |= copy_files(log=log)

    if log:
        msg = (
            'Remember to adjust SSHAIL_SSH_HOST at /etc/sshail/conf.ini\n'
            'Also you need to define your sshails at /etc/sshail/sshails.yml'
        )
        log.info(msg)

        if not error:
            log.info("SSHail deploy Finished")
        else:
            log.error("SSHail failed to deloy")

    return error
