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

resolve_service()
{
    if [ "${DNS_SERVICE}" == "" ]; then
        echo "no DNS service found"
        exit 1
    fi
    local service=$1;
    echo "setting "$service" service ..."
    result=`curl http://${DNS_SERVICE}/v1/services/${service}`
    raw_ip=$(echo $result | awk -F, '{print $3}' | awk -F: '{print $2}')
    RESOLVE_IP=${raw_ip//\"/}
    RESOLVE_IP=${RESOLVE_IP// /}
    raw_port=$(echo $result | awk -F, '{print $4}' | awk -F: '{print $2}' | awk -F} '{print $1}' )
    RESOLVE_PORT=${raw_port//\"/}
    RESOLVE_PORT=${RESOLVE_PORT// /}
}

if [ "${DB_SERVICE}" != "" ]; then
    echo "setting DB service ..."
    resolve_service ${DB_SERVICE}
    export DB_PROXY_PORT_5432_TCP_ADDR=$RESOLVE_IP
    export DB_PROXY_PORT_5432_TCP_PORT=$RESOLVE_PORT
fi
if [ "${REDIS_SERVICE}" != "" ]; then
    echo "setting redis service ..."
    resolve_service ${REDIS_SERVICE}
    export CELERY_REDIS_1_PORT_6379_TCP_ADDR=$RESOLVE_IP
    export CELERY_REDIS_1_PORT_6379_TCP_PORT=$RESOLVE_PORT
fi
if [ "${CACHE_SERVICE}" != "" ]; then
    echo "setting cache redis service ..."
    resolve_service ${CACHE_SERVICE}
    export MEMCACHED_ADDR=$RESOLVE_IP
    export MEMCACHED_PORT=$RESOLVE_PORT
fi

echo "connecting to cache ..."
wait_tcp_dependency ${MEMCACHED_ADDR} ${MEMCACHED_PORT}
echo "connecting to redis ..."
wait_tcp_dependency ${CELERY_REDIS_1_PORT_6379_TCP_ADDR} ${CELERY_REDIS_1_PORT_6379_TCP_PORT}
echo "connecting to db ..."
wait_tcp_dependency ${DB_PROXY_PORT_5432_TCP_ADDR} ${DB_PROXY_PORT_5432_TCP_PORT}

# do database migration
python manage.py makemigrations
python manage.py migrate
# do translation
python manage.py compilemessages
# collect static files
python manage.py collectstatic --noinput
# run server
export CELERY_BROKER_URL=redis://${CELERY_REDIS_1_PORT_6379_TCP_ADDR}:${CELERY_REDIS_1_PORT_6379_TCP_PORT}
# python manage.py runserver 0.0.0.0:${SERVICE_PORT}
uwsgi --ini uwsgi.ini
