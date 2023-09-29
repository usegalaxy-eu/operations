# SSL Certificate expansion for Galaxy EU

This README outlines the process for expanding the Galaxy EU SSL certificate to include a new wildcard domain, for example: `*.aqua.usegalaxy.eu`.

# Using Route 53 and DNS challenge

## Step 1: Update Playbook

Create a pull request in [infrastructure-playbook repo](https://github.com/usegalaxy-eu/infrastructure-playbook) to add a new wildcard domain to the list of domains in the [`sn06.yml` playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sn06.yml#L34C5-L34C17). For example, to add `*.aqua.usegalaxy.eu` to the list of domains, add the following line to the playbook variable `server_names` and submit a pull request like [shown here in this PR](https://github.com/usegalaxy-eu/infrastructure-playbook/pull/916):

```yaml
- "*.aqua.usegalaxy.eu"
```

## Step 2: Create a Backup

Before making any changes, it's essential to create a backup of the current SSL certificates

1. `/etc/letsencrypt/live/usegalaxy/`
2. `/etc/ssl/certs/fullchain.pem`
3. `/etc/ssl/user/privkey-nginx.pem`

## Step 3: Expand the Current Certificate

Run the following command to expand the current certificate with the new domain `*.aqua.usegalaxy.eu`. This command should be executed as the root user, and AWS credentials are assumed to be available in the root's home directory (see [here](https://certbot-dns-route53.readthedocs.io/en/stable/) for details on AWS creds). AWS DNS is used because is very easily scriptable.

_Note: The list of domains (values for option `-d`) can be obtained from the current certificate by running the command from Step 4 or it can be gathered from the console logs of the recent Jenkins job (sn06 project under playbooks)_

```bash
/opt/certbot/bin/certbot certonly --non-interactive --dns-route53 -m security@usegalaxy.eu --agree-tos -d usegalaxy.eu,*.usegalaxy.eu,galaxyproject.eu,*.galaxyproject.eu,*.interactivetoolentrypoint.interactivetool.usegalaxy.eu,*.interactivetoolentrypoint.interactivetool.live.usegalaxy.eu,*.interactivetoolentrypoint.interactivetool.test.usegalaxy.eu,*.aqua.usegalaxy.eu --expand
```

_Note: If you are not sure you can append the above command with `--dry-run` and `-v` to perform a dry run and check if everything looks fine_

## Step 4: Verify the inclusion of the new domain

```bash
openssl x509 -in /etc/letsencrypt/live/usegalaxy.eu/fullchain.pem -text -noout | grep DNS
```

or

```bash
/opt/certbot/bin/certbot certificates
```

## Step 5: Copy and Replace Certificates

After generating and testing the new certificates, you can replace the existing certificates in the following locations:

- Fullchain: `/etc/ssl/certs/fullchain.pem`
- Private Key: `/etc/ssl/user/privkey-nginx.pem`

_Note: New certificate is available here `/etc/letsencrypt/live/usegalaxy/fullchain.pem`, and the private key is available here `/etc/letsencrypt/live/usegalaxy/privkey.pem`_

```bash
cp /etc/letsencrypt/live/usegalaxy/fullchain.pem /etc/ssl/certs/fullchain.pem
cp /etc/letsencrypt/live/usegalaxy/privkey.pem /etc/ssl/user/privkey-nginx.pem
```

## Step 6: Reload Nginx

Don't forget to reload the Nginx server after renewing or expanding the SSL certificate to apply the changes.

```bash
systemctl restart nginx
```
