# Creating and editing an encrypted file using Ansible Vault
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
