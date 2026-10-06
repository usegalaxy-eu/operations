# Traefik

See [Add a new Traefik subdomain](../runbooks/traefik-new-subdomains.md) and [Troubleshooting Traefik](../troubleshooting/traefik.md).
[Traefik](https://doc.traefik.io/traefik/v3.0/) is used as a reverse proxy, certificate manager and loadbalancer for `sn09` and `sn07`.
It is deployed using an [ansible-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/pull/1257) which uses [usegalaxy-eu's Traefik role](https://github.com/usegalaxy-eu/ansible-Traefik). This role internally initializes a swarm cluster on the target host, creates secrets, the specified network and docker swarm services.  
Docker swarm was used for mainly two reasons:
1. Secret handling: Secrets are not saved inside env files, but are encrypted on disk and only available to the container they are attached to.
2. Scalability and future failover safe deployments: By using Docker swarm you can quite easily add a second proxy node and use e.g. [keepalived](https://www.keepalived.org/) as ingress.
3. Features: Traefik comes with many options for middlewares and Plugins. If you would like, for instance, to block certain IP ranges, this could be easily done using a [plugin](https://plugins.traefik.io/plugins).

## Basics
|                    |                             |
| ------------------ | --------------------------  |
| Default user       | `rocky`                     |    
| IP                 | `132.230.103.37`            | 
| Host               | `traefik.galaxyproject.eu`  |   
| Traefiks logs      | `/var/log/traefik`          |  

To have a pretty output use `hl`:
~~~
sudo ./hl /var/log/traefik/traefik./glog --follow
~~~
The machine is a ESXi VM. The University provides this fancy [dashboard](https://vcsa-rz.intra.uni-freiburg.de/). Log in with your university handle and password.
### Docker swarm basics
`docker service ls` shows the "services" which are similar to the ones in kubernetes.  
`docker service rm` deletes the service and all its respective containers, in case you would like to start from clean slate.  
`docker service logs` would not work with Traefik, because it writes directly to `/var/log/traefik`  


