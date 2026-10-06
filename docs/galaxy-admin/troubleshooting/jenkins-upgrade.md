# Troubleshooting

See [Upgrade or restore Jenkins](../runbooks/jenkins-upgrade-and-restore.md) for the complete runbook.
A few errors I ran into:

- be careful with fstab – if you change a FS that is defined there and `nofail` is not specified, the server will crash on reboot
- if the website is not reachable, check if Jenkins is running, if it is running, it could be probably NGINX or the firewall. Test the ports with `telnet build.galaxyproject.eu 80` and 443. 80 needs to be open for TLS-domain-challenge done by certbot.
- if Jenkins crashes on startup and without any logs, it might be a false command-line option, try without
