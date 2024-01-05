# all networking topics
## Postgres with tailscale
Assuming your postgres is already running.
1. Install tailscale on the postgres server and the machines that should have access
2. Generate a key in the tailscale or headscale web interface and use `sudo tailscale up --auth-key <your-key>
3. Make sure the ACLs are configured in a way that the other machines can access `5432` on the postgres server
4. Create firewall rules (described for firewalld here)
   1. `firewall-cmd --new-zone=tailscale --permanent`
   2. `firewall-cmd --zone=tailscale --add-interface=tailscale0 --permanent`
   3. `firewall-cmd --zone=tailscale --add-service=5432/tcp --permanent`
   4. `firewall-cmd --reload`
5. Add/Change the following line in your postgresql.conf: `listen_addresses: '*'`
6. Add tailscale's CIDR to your `pg_hba.conf`: `host all all 100.64.0.0/10 md5`
7. Restart the postgres service
