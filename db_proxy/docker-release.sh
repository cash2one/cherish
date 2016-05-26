#!/bin/bash

REGISTRY="docker.zuoyetong.com.cn:8888/"
IMAGE_NAME="account_db_proxy"
VERSION="`date +%Y%m%d%H%M`"

IMAGE="${REGISTRY}${IMAGE_NAME}:${VERSION}"

docker build -t ${IMAGE} .
if [ "$?" != "0" ]; then
    echo "${IMAGE} build fail"
    exit 1
fi

docker tag -f ${REGISTRY}${IMAGE_NAME}:${VERSION} ${REGISTRY}${IMAGE_NAME}:latest

if [ "$1" == "push" ]; then
    docker push ${IMAGE}
    if [ "$?" != "0" ]; then
        echo "${IMAGE} push fail"
        exit 1
    fi
fi
