
## Galaxy Job handling 

Reassign jobs from handler 11 to handler 3 with gxadmin:

```bash
gxadmin tsvquery queue-detail-by-handler handler_main_11  | cut -f1 | xargs -I{} -n1 gxadmin mutate reassign-job-to-handler {} handler_main_3 --commit

```

-----

Change htcondor labels on-the-fly:

```bash
sed -i 's/"compute"/"dockerhack"/g' /etc/condor/condor_config.local; systemctl reload condor
```

Test with:

```bash
condor_status -autoformat Machine GalaxyGroup GalaxyDockerHack | grep hack | sort -u
```
