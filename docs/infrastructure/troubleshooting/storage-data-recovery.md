# Recovering data
If you get the history ID, the following query will help you to see the datasets' object_store_id, UUIDs and state:
~~~sql
SELECT d.object_store_id, d.uuid, d.deleted, d.purged FROM history_dataset_association h INNER JOIN dataset d ON h.dataset_id = d.id where h.history_id = <history_id>
~~~
Now you can export the UUIDs separated by `object_store_id`:
~~~sql
\copy (SELECT uuid FROM history_dataset_association h INNER JOIN dataset d ON h.dataset_id = d.id where h.history_id = <history_id> and d.object_store_id = 'files10') to '/tmp/abc_lost_files_files10.tsv';
~~~
This file you can use to search the files on NFS or S3:
## NFS
~~~sh
root@sn09:/home/centos$ while read uuid; do bash search_s3_unix.sh "$uuid" /data/dnb-ds03/galaxy_db/files; done </tmp/abc_lost_files_files10.tsv
~~~
## S3

~~~sh
root@sn09:/home/centos$ while read uuid; do bash search_s3.sh "$uuid"; done </tmp/abc_lost_files_s3.tsv > /tmp/abc_lost_files_s3_found
~~~
Recover using
~~~sh
root@sn09:/home/centos$ while read uuid; do ./mc cp "$file" /data/dnb01/recovered_data/<user_name>; done </tmp/abc_lost_files_s3_found
~~~
