# New subdomains
See the [Traefik reference](../reference/traefik.md) for deployment details and [Troubleshooting Traefik](../troubleshooting/traefik.md) when the router does not appear.
To add new subdomains, add a new line to the file `files/traefik/rules/template-subdomains.yml` in the [infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook) repo. The language there is a `go` template for a `yaml` file, which might look similar to ansible at first. (In case you wonder about the syntax).  
The line should look like the ones above, like this scheme:
~~~
{{template "subdomain" "<your-subdomain-name>"}}
~~~
Be careful, the word `subdomain` in the second colum needs to stay literaly "subdomain", only the 3rd column is changed to the new subdomain, but without any `.usegalaxy.eu`.  
Once this is deployed, Traefik will automatically create a router for it and fetch certificates for the subdomain as well as a wildcard certificate for ITs.  
If you did everything correctly, the new router appears on Traefik's [dashboard](https://traefik.springhare-dinosaur.ts.net/dashboard/#/).

