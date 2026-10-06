# Migrating storage

Galaxy has for every storage backend, defined in `config/object_store_conf.xml|yml, an ID specified. This ID ends up in the `datasets` table of Galaxy SQL database.

If we want to migrate old storages from `/data/0/galaxy_db/files/` to `/data/1/galaxy_db/files/` the following steps worked well:

```bash
rclone copy -v -P --transfers 8 /data/0/galaxy_db/files/ /data/1/galaxy_db/files/
rsync -auvi --stats --progress /data/0/galaxy_db/files/ /data/1/galaxy_db/files/
```

Using `rclone` before `rsync` can speed up the file-transfer. `Rclone` can copy data in parallel and `rsync` fixes up the permission or symlinks etc when needed.

When the data is copied, we need to update the `object_store_id` in the DB and then we can delete the data on the old storage.
```sql
UPDATE dataset SET object_store_id = 'files1' WHERE object_store_id = 'files0';
```

