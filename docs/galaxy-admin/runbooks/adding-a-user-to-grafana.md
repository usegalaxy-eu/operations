# Adding a User to Grafana

1. They should [login](https://stats.galaxyproject.eu) using GitHub auth.
    - Note that they must be a member of an [approved organisation](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/39d5b7e86b4f45acba53adb965b11b63700327ad/group_vars/grafana.yml#L119).  (Note that this link is to a specific revision where I could be sure the line number was correct, please check against `master`)
2. (As an admin) Open [the user list](https://stats.galaxyproject.eu/admin/users/)
3. Find them and "edit"
4. Under "Organizations" type "Main" and select the main organisation that shows up, adding them as the appropriate role.
