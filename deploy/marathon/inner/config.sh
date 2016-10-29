#!/usr/bin/env sh
IMAGE_VERSION=${IMAGE_VERSION:-"201607261518"}
DEPLOY_NAME="account-center"
APP_GROUP="http://marathon-inner.zuoyetong.com.cn/v2/apps/$DEPLOY_NAME"
APP_LIST="db cache redis celery-worker web rproxy"
