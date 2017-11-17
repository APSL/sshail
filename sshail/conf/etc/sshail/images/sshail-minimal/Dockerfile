FROM ubuntu:16.04

# Inspired from https://docs.docker.com/engine/examples/running_ssh_service/
RUN apt-get -qq update && \
    apt-get -qq install -y openssh-server

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

COPY entrypoint.sh /

# Directory for other images to extend entrypoint funcionality
RUN mkdir -p /entrypoint.d

EXPOSE 22

# Prfixed with SSHAILENV to avoid colisons with other
# env variables.
#ENV \
#    SSHAILENV_USER= \
#    SSHAILENV_USER_CRYPT= \
#    SSHAILENV_USER_HOME= \
#    SSHAILENV_USER_UID= \
#    SSHAILENV_USER_GID=

ENTRYPOINT ["/entrypoint.sh"]
