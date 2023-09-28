# SSL Certificate expansion for Galaxy EU

This README outlines the process for expanding the Galaxy EU SSL certificate to include a new wildcard domain, for example: `*.aquainfra.usegalaxy.eu`.

# Using Route 53 and DNS challenge

## Step 1: Create a Backup

Before making any changes, it's essential to create a backup of the current SSL certificates

1. `/etc/letsencrypt/live/usegalaxy/`
2. `/etc/ssl/certs/fullchain.pem`
3. `/etc/ssl/user/privkey-nginx.pem`

## Step 2: Expand the Current Certificate

Run the following command to expand the current certificate with the new domain `*.aquainfra.usegalaxy.eu`. This command should be executed as the root user, and AWS credentials are assumed to be available in the root's home directory (see [here](https://certbot-dns-route53.readthedocs.io/en/stable/) for details on AWS creds).

_Note: The list of domains (values for option `-d`) can be obtained from the current certificate by running the command from Step 3 or it can be gathered from the console logs of the recent Jenkins job (sn06 project under playbooks)_

```bash
/opt/certbot/bin/certbot certonly --non-interactive --dns-route53 -m security@usegalaxy.eu --agree-tos -d usegalaxy.eu,*.usegalaxy.eu,galaxyproject.eu,*.galaxyproject.eu,*.interactivetoolentrypoint.interactivetool.usegalaxy.eu,*.interactivetoolentrypoint.interactivetool.live.usegalaxy.eu,*.interactivetoolentrypoint.interactivetool.test.usegalaxy.eu,*.aquainfra.usegalaxy.eu --expand
```

## Step 3: Verify the inclusion of the new domain

```bash
openssl x509 -in /etc/letsencrypt/live/usegalaxy.eu/fullchain.pem -text -noout | grep DNS
```

## Step 4: Copy and Replace Certificates

After generating and testing the new certificates, you can replace the existing certificates in the following locations:

- Fullchain: `/etc/ssl/certs/fullchain.pem`
- Private Key: `/etc/ssl/user/privkey-nginx.pem`

_Note: New certificate is available here `/etc/letsencrypt/live/usegalaxy/fullchain.pem`, and the private key is available here `/etc/letsencrypt/live/usegalaxy/privkey.pem`_

```bash
cp /etc/letsencrypt/live/usegalaxy/fullchain.pem /etc/ssl/certs/fullchain.pem
cp /etc/letsencrypt/live/usegalaxy/privkey.pem /etc/ssl/user/privkey-nginx.pem
```

## Step 5: Reload Nginx

Don't forget to reload the Nginx server after renewing or expanding the SSL certificate to apply the changes.

```bash
systemctl restart nginx
```

## Step 6: Update Playbook

Once the certificate is successfully expanded, update the playbook to include the new subdomain, `*.aquainfra.usegalaxy.eu` in [here](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sn06.yml#L34)

# Using webroot

The only difference is the step 2 from above and rest of them are the same

## Step 2: Expand the Current Certificate when using webroot instead of DNS challenge
_Note: the path `/etc/nginx/_well-known_root` should exist_

``` bash
/opt/certbot/bin/certbot certonly --non-interactive --webroot -w /etc/nginx/_well-known_root -m security@usegalaxy.eu --agree-tos -d usegalaxy.eu,*.usegalaxy.eu,galaxyproject.eu,*.galaxyproject.eu,*.interactivetoolentrypoint.interactivetool.usegalaxy.eu,*.interactivetoolentrypoint.interactivetool.live.usegalaxy.eu,*.interactivetoolentrypoint.interactivetool.test.usegalaxy.eu,*.aquainfra.usegalaxy.eu --expand
```