# How to debug
See the [Traefik reference](../reference/traefik.md) and [Add a new Traefik subdomain](../runbooks/traefik-new-subdomains.md) for planned changes.
## 🚑 Galaxy not reachable
In order to bridge the debug time, you can install HAProxy on Traefik and try [this config](https://gist.github.com/meanevo/f962a8fa5763862ab6cd94addbc4dd8d)
## usegalaxy.eu /subdomain is showing a plain `404 not found`
Most likely something happened to the router.
- Check the [dashboard](https://traefik.springhare-dinosaur.ts.net/dashboard/#/) via tailscale
- If all routers look fine, check if something happened to the rulefile in `files/traefik/rules/` `usegalaxy-eu-router.yml` for usegalaxy.eu and `template-subdomains.yml` for subdomains. Take a close look at the `HostRegexp` rule.
- Less likely: check that the `servers` in `usegalaxy-eu-service.yml` are correct and reachable.
## `Bad Gateway` error
- One headnode unhealthy? You can test with e.g. `sn07.galaxyproject.eu` directly. Traefik should automatically skip unhealth hosts, see the [dashboard](https://traefik.springhare-dinosaur.ts.net/dashboard/#/) and [docs](https://doc.traefik.io/traefik/v3.0/routing/services/#health-check)
- Can be faulty certificates. When checked everything else, make a backup of `/etc/traefik/acme.json` and delete all its contents (not the file itself), then restart Traefik using `docker restart <Traefik container name>`
- Service configuration might be faulty: check `usegalaxy-eu-service.yml`

## `no available server`
This could mean that either
- both headnodes are down
- Traefik was unable to get a response when doing the [healthCheck](https://doc.traefik.io/traefik/v3.0/routing/services/#health-check)
- in the latter case, check if the DNS inside the container works. If it fails, tailscale might be the issue.
~~~
sudo tailscale up --accept-dns=false --advertise-tags=tag:critical
docker restart <Traefik container name>
~~~
This should not be necessary, because it is set in `group_vars/all.yml`

## Self signed certificate warning
Could only appear when many certs have to be fetched newly at the same time.  
`AWS route53` has a harsh rate limit of 5 req/s, if Traefik tries to create and check the `TXT records` during `DNS-01 challenge` for all subdomains, this could result in >100 req/s. It will take some time and Traefik will get more and more certs. If you see error messages after 1h, you can try to restart Traefik.
## Letsencrypt i/o error
Probably a egress issue with Docker networks. Recreating the bridge helped:
~~~
# systemctl stop docker
# iptables -t net -F
# ip link set docker0 down
# brctl delbr br100
# systemctl start docker
~~~
