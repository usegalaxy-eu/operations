# galaxy-ncdu / dusage

This is a pair of scripts that leverages `ncdu(1)` for monitoring
block usage per directory. One, `galaxy-ncdu` is supposed to be
run daily on a file server host to build a database for the share
to be monitored (edit the script to set the path of the share) and
the other, `dusage` is supposed to be run on the client for finding
that pesky job that is filling up the share again.

Note that `dusage` parses the autofs map `/etc/auto.data` to find
the names of shares currently in use and requires that file to be
present and up-to-date.

CAVEAT EMPTOR: When run against directories containing too many
files (on the order of 10^6 or greater), `galaxy-ncdu` might put
an undue load on the file server, even when run locally; for this
reason its use has been discontinued as of early 2025 but the pair
of scripts is preserved here nonetheless.

