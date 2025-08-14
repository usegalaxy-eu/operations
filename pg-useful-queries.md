# PG Useful Queries

This is a random collection of PG SQL queries that people have found
useful in the past, ranging from the trivial to the mildly complex.


## Sessions / Transactions

### List current user sessions, sort by activity

```
SELECT pid,datname, usename, application_name, client_addr, state, state_change
FROM pg_stat_activity
WHERE usename IS NOT NULL
ORDER BY state_change DESC;
```


### List current *active* user sessions, sort by activity

```
SELECT pid,datname, usename, application_name, client_addr, state, state_change
FROM pg_stat_activity
WHERE usename IS NOT NULL
  AND state NOT LIKE 'idle%'
ORDER BY state_change DESC;
```


### Show number of current connections, group by source IP

```
SELECT COUNT(*), client_addr
FROM pg_stat_activity
GROUP BY client_addr
ORDER BY COUNT(*) DESC;
```


## Locks

### Show information on currently held locks

**NOTE:** This query returns information *on the currently connected DB only!*

```
SELECT sub1.count,
       sub1.mode,
       sub1.relation,
       cls.relname
FROM ( SELECT COUNT(*) as count, relation, mode
       FROM pg_locks
       WHERE relation IS NOT NULL
       GROUP BY database,relation,mode ORDER BY COUNT(*) DESC LIMIT 30 ) as sub1,
       pg_class as cls
WHERE sub1.relation = cls.oid
ORDER BY sub1.count DESC;
```


## Dead tuples

### Show number of live / dead rows per table, order by number of dead rows

**NOTE:** This query returns information *on the currently connected DB only!*

```
SELECT
  relname AS table,
  n_live_tup AS live_rows,
  n_dead_tup AS dead_rows,
  ROUND((n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0)) * 100, 2)
    AS dead_ratio
FROM pg_stat_user_tables
WHERE n_live_tup + n_dead_tup > 0
ORDER BY dead_rows DESC, dead_ratio DESC;
```

(Alternatively, sort by `dead_ratio DESC` *only*.)


