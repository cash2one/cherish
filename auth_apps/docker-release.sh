#!/bin/bash
REGISTRY="docker.zuoyetong.com.cn/account_center/"
IMAGE_NAME="account_web"

ACTION=$1
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "git branch: "$BRANCH
COMMIT_ID=$(git rev-parse $BRANCH)
echo "git commit: "$COMMIT_ID
VERSION="$BRANCH.${COMMIT_ID:0:8}"
IMAGE="${REGISTRY}${IMAGE_NAME}:${VERSION}"

EXIST=$(docker images | grep "${REGISTRY}${IMAGE_NAME}" | grep "${VERSION}")
if [[ "$EXIST" == "" ]]; then
    echo "build new image ..."
    docker build -t ${IMAGE} .
    if [ "$?" != "0" ]; then
        echo "${IMAGE} build fail"
        exit 1
    fi
    docker tag -f ${REGISTRY}${IMAGE_NAME}:${VERSION} ${REGISTRY}${IMAGE_NAME}:latest
fi

if [ "$ACTION" == "push" ]; then
    echo "push image to repo ..."
    docker push ${IMAGE}
    if [ "$?" != "0" ]; then
        echo "${IMAGE} push fail"
        exit 1
    fi
elif [ "$ACTION" == "rm" ]; then
    echo "delete local image"
    docker rmi ${IMAGE}
fi
