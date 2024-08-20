# Email related topics
## Email routing for usegalaxy.eu
We are currently (8/2024) using forwardemail.net for email routing using Björn's account.  
All incoming email routing is set via that account in forwardemail.net's web interface.
Currently we have the following routes:
| route          |  receiver                                   |
| -------------- | ------------------------------------------- |
| * (catch all)  |     `galaxy at informatik.uni-freiburg.de`  |
| contact        |     `galaxy at informatik.uni-freiburg.de`  |
| bugs           |     `galaxy at informatik.uni-freiburg.de`  |
| security       | `galaxy-ops at informatik.uni-freiburg.de`  |
| admin          | `galaxy-ops at informatik.uni-freiburg.de`  |

However, bug reports are sent by Galaxy automatically to `galaxy-no-reply at informatik.uni-freiburg.de`

### Send from email alias (Thunderbird)
If you want to send email with one of those aliases, you need to can add them to thunderbird following this [guide in English](https://support.mozilla.org/en-US/kb/configuring-email-aliases) or [this guide in German](https://www.rz.uni-frankfurt.de/75346969/Alias_einrichten?). Using the following settings:

| Field                 | Setting                |
| --------------------- | ---------------------- |
| Name                  | Your Name              |
| Email                 | \<alias\>@usegalaxy.eu |
| Reply address         | \<alias\>@usegalaxy.eu |
| Server Name           | smtp.forwardemail.net  |
| Port                  | 465                    |
| Connection security   | SSL/TLS                |
| Authentication method | Normal password        |
| User name             | \<alias\>@usegalaxy.eu |

The password is asked when you send the first email. You find it in [the vault in infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/secret_group_vars/mail.yml). To view it, you need to clone the repo, install ansible, create a file in the repo's directory named vault_password.txt and insert the password you get from e.g. Björn. Then you can run `ansible-vault view secret_group_vars/mail.md`.

