# Investigating large RabbitMQ queue files

Sometimes the space gets very tight in the rabbit hole and you find files that are large, even up to multiple GB:
~~~
14GB /opt/rabbitmq/data/mnesia/rabbit@mq02/msg_stores/vhosts/D9TR3BK9230KDSJSHK8SQ6Y7XE7R/queues/73X2Y1RGJSKAJOJHXAIOVHM
~~~
But beware make sure you are cutting the right ties here, this file could be important for Galaxy to function. To see if it actually belongs to a galaxy queue
use this erratic Erlang snippet and try galaxy internal and external, then compare the resulting path:
~~~
mq02:/# rabbitmqctl eval 'VHost = <<"galaxy">>, QName = <<"galaxy.internal">>, VDir = rabbit_vhost:msg_store_dir_path(VHost), <<Num:128>> = erlang:md5(<<"queue", VHost/binary, QName/binary>>), QDir = rabbit_misc:format("~.36B", [Num]), filename:join([VDir, "queues", QDir]).'
~~~

See the [Celery runbook](../runbooks/celery.md#chapter-one-down-the-rabbit-hole) for RabbitMQ setup and connectivity.
