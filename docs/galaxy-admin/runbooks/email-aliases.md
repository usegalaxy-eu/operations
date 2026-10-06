# Send from email alias (Thunderbird)
See [Email routing for usegalaxy.eu](../reference/email-routing.md) for the available aliases.
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

The password is asked when you send the first email. 
## Password for admins
You find it in [the vault in infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/secret_group_vars/mail.yml). To view it, you need to clone the repo, install ansible, create a file in the repo's directory named vault_password.txt and insert the password you get from e.g. Björn. Then you can run `ansible-vault view secret_group_vars/mail.md`.
## Password for everyone else
Ask one of the admins for the password.:wink:
