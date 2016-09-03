#!/bin/bash

# input: tcp_addr, tcp_port
wait_tcp_dependency()
{
    local tcp_addr=$1;
    local tcp_port=$2;
    local testing_url="tcp://${tcp_addr}:${tcp_port}"

    # assign fd automatically
    # refer to http://stackoverflow.com/questions/8295908/how-to-use-a-variable-to-indicate-a-file-descriptor-in-bash
    while ! exec {id}<>/dev/tcp/${tcp_addr}/${tcp_port}; do
        echo "$(date) - trying to connect to ${testing_url}"
        sleep 1
    done   
}

echo "connecting to cache ..."
wait_tcp_dependency ${MEMCACHED_ADDR} ${MEMCACHED_PORT}
echo "connecting to redis ..."
wait_tcp_dependency ${REDIS_PORT_6379_TCP_ADDR} ${REDIS_PORT_6379_TCP_PORT}
echo "connecting to db ..."
wait_tcp_dependency ${DB_PORT_3306_TCP_ADDR} ${DB_PORT_3306_TCP_PORT}

echo "run celery worker ..."
celery --app=auth_apps.celery:app worker --loglevel=DEBUG --autoreload