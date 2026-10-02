[![documentation](https://img.shields.io/badge/documentation-online-blue)](https://usegalaxy-eu.github.io/operations/)

# Operations Manual for usegalaxy.eu

- [Custom Subdomain](./galaxy-admin/subdomains.md)
- [Interactive Tools](./galaxy-admin/interactive_tools.md)
- [Update a Tool](https://github.com/usegalaxy-eu/usegalaxy-eu-tools)
- [Galaxy Europe Services](./kvm/services.md)
- [Bare metal nodes](./infrastructure/bare_metal.md)
- [Traefik](./galaxy-admin/traefik.md)
- [Configuring multi-GPU HTCondor nodes](./htcondor/multi-gpu-single-node-htcondor.md)

Galaxy Admin:

- [Upgrade Procedures](./galaxy-admin/upgrade.md)
- [Rebasing when upstream gets backports](./galaxy-admin/rebasing.md)
- [Process Management](./archived/procmgmt.md)
- [TIaaS Requests](./galaxy-admin/tiaas.md)
- [Jobs](./galaxy-admin/debug/jobs.md)
- [Monitoring](./archived/monitoring.md)
- [Mixed Notes](./galaxy-admin/debug/notes.md)

KVM Infrastructure:

- [KVM Infrastructure (Terraform + libvirt)](./kvm/README.md)
- [Galaxy Europe Services](./kvm/services.md)
- [Celery](./galaxy-admin/celery.md)

The former bwCloud documentation has been moved to [archived/cloud/](./archived/cloud/).


This and That:
- [Miscellaneous stuff](./miscellanea/)

## Read-only Fridays

- **NO EXCEPTIONS**
- Do not merge things to the playbook repositories that will be auto-applied
- Do not do any manual systems administration
- Consider writing documentation or more test cases instead.

## Adding a User to Grafana

1. They should [login](https://stats.galaxyproject.eu) using GitHub auth.
    - Note that they must be a member of an [approved organisation](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/39d5b7e86b4f45acba53adb965b11b63700327ad/group_vars/grafana.yml#L119).  (Note that this link is to a specific revision where I could be sure the line number was correct, please check against `master`)
2. (As an admin) Open [the user list](https://stats.galaxyproject.eu/admin/users/)
3. Find them and "edit"
4. Under "Organizations" type "Main" and select the main organisation that shows up, adding them as the appropriate role.

## (Re-)sending activation links

Some users do not get the activation email or are unable to find it. On request we can generate the link with the
following procedure:

```bash
cd /opt/galaxy/server/
. ../venv/bin/activate
python /data/gxmnt/galaxy-dist/scripts/activation_link.py -c ~/config/galaxy.ini -e <their email>
```

## Creating and editing an encrypted file using Ansible Vault
Ansible Vault encrypts variables and files to protect sensitive content such as passwords or keys rather than leaving it visible as plaintext in playbooks or roles.To use Ansible Vault you need one or more passwords to encrypt and decrypt content. If you store your vault passwords in a third-party tool such as a secret manager, you need a script to access them. Use the passwords-with the ‘ansible-vault’ command line tool to create and view encrypted variables, create encrypted files, encrypt existing files, or edit, re-key, or decrypt files.

1. Clone [our repository](https://github.com/usegalaxy-eu/infrastructure-playbook).
2. Navigate to Ansible vault directory `cd infrastructure-playbook/secret_group_vars/`
3. Create a new branch or checkout to the branch you want to switch to, e.g.(‘dp_keycloak’)
4. Use command `ansible-vault create keycloak.yml` to create new encrypt file.
5. Then ansible asks for:

        New Vault password:

        Confirm New Vault password:
   It is recommended to use the previously set Vault password for smooth running of playbook
6. The newly created encrypt file (‘keycloak.yml’)  enables us to enter data or enter lines of code before encrypted.
7. The content in the encrypted files can be read by command `ansible-vault view keycloak.yml` and can be edited by the command `ansible-vault edit  keycloak.yml` followed by entering the given Vault password.
8. Update the branch pushing commits `git push`
