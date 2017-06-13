from crypt import crypt
import random, string

from click import prompt

def randomword(length=16):
    return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase) for i in range(length))


def addsshail(
        user=None,
        real_user=None,
        basic_passwd=None,
        user_crypt=None,
        commit=False,
        log=None,
    ):

    if not user:
        user = prompt(
                    "Container (and HTTP API) username",
                    type=str,
                )

    if not basic_passwd:
        basic_passwd = prompt(
                        "HTTP API password",
                        type=str,
                        default=False,
                    )

        if not basic_passwd:
            basic_passwd = randomword()
            print("No password specified generating one: {}".format(basic_passwd))

    if not real_user:
        msg = "System user to inherit permissions (default {})"
        real_user = prompt(
                        msg.format(user),
                        type=str,
                        default=False,
                    ) or user

    if not user_crypt:
        passwd = prompt(
                    "Container password (clear)",
                    type=str,
                    default=False,
                )
        if not passwd:
            passwd = randomword()
            print("No password specified generating one: {}".format(passwd))

        user_crypt = crypt(passwd, "$6${}$".format(randomword(8)))

    if not commit:
        print("Add those lines to your /etc/sshail/sshails.yml")
        print(
            "    -\n"
            "        user: '{user}'\n"
            "        real_user: '{real_user}'\n"
            "        basic_passwd: '{basic_passwd}'\n"
            "        user_crypt: '{user_crypt}'\n"
            "".format(
                    user=user,
                    real_user=real_user,
                    basic_passwd=basic_passwd,
                    user_crypt=user_crypt,
            )
        )

    else:
        pass # TODO write to the yaml

    return False
