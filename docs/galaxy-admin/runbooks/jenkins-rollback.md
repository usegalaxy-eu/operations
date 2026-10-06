# How to roll-back Jenkins

Find jenkins.war, in our case its at `/usr/share/java`. Rename the `jenkins.war` file:

```bash
/usr/share/java$ mv jenkins.war jenkins.war_2.375 
```

Get older Jenkins version and restart.

```bash
/usr/share/java$ wget https://updates.jenkins.io/download/war/2.374/jenkins.war
/usr/share/java$ systemctl restart jenkins
```
*or*
Instead of rollback try the newest release with
`sudo yum update jenkins`

