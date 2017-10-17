# -*- coding: utf-8 -*-

from sys import version_info

from setuptools import setup

if version_info.major != 3:
    raise OSError("Python 3 is required")

INSTALL_REQUIRES = [
    'click==6.7',
    'docker',
    'Flask==0.12',
    'python-dateutil==2.6.1',
    'PyYAML==3.12',
]

setup(
    name='sshail',
    version='0.0.7',
    include_package_data=True,
    packages=[
        'sshail',
    ],
    url=u"https://github.com/apsl/sshail",
    license='GPLv3',
    install_requires=INSTALL_REQUIRES,
    entry_points="""
        [console_scripts]
        sshail=sshail.main:sshail
    """,
    author=u"Bartomeu Miro Mateu",
    author_email=u"bmiro@apsl.net",
    description=u"Easy SSH jails using Docker"
)

