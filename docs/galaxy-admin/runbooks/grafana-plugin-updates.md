# Grafana

Installing or updating Grafana plugins can be done via the grafana-cli tools. Please note that the
plugin folder is mounted from a volume and resides in `/vdb/grafana/plugins/`

```console
ssh stats.galaxyproject.eu
sudo grafana-cli --pluginsDir /vdb/grafana/plugins/ plugins update grafana-worldmap-panel
sudo /etc/init.d/grafana-server restart
```


