#!/usr/bin/env sh
set -e
IMAGE_VERSION=${IMAGE_VERSION:-"201607261518"}
DEPLOY_NAME="account-center-online"
APP_GROUP="http://marathon-online.zuoyetong.com.cn/v2/apps/$DEPLOY_NAME"
APP_LIST="db cache redis celery-worker web rproxy"
