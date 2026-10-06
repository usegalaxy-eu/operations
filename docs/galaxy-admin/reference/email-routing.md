# Email routing for usegalaxy.eu
See [Send from email alias (Thunderbird)](../runbooks/email-aliases.md) for client setup.
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

