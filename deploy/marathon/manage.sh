#!/usr/bin/env bash
set -e

ACTION=$1
PLATFORM=$2
SINGLE_APP=$3
ACTION_LIST="list put delete"
PLATFORM_LIST="inner online"
if ([[ "$ACTION" =~ "$ACTION_LIST" ]] && [[ "$PLATFORM" =~ "$PLATFORM_LIST" ]]) ; then
    echo "USAGE: $0 <[list|put|delete]> <platform> [<app>]"
    exit 1
fi

source $PLATFORM/config.sh

run_single_app() {
    action=$1
    platform=$2
    app=$3
    echo $app
    if [[  "$action" == "put" ]]; then
        data=`sed "s~DEPLOY_NAME~${DEPLOY_NAME}~g;s~IMAGE_VERSION~${IMAGE_VERSION}~g;"  "$platform/$app".json`
        echo $data
        # update the configuration of an app
        curl -X PUT "$APP_GROUP/$app?force=true" --data @<(echo $data) -H "Content-type: application/json"
        sleep 5
    elif [[ "$action" == "delete" ]]; then
        curl -X DELETE "$APP_GROUP/$app"
    elif [[ "$action" == "list" ]]; then
        # list out the apps availale
        echo "info:"
        curl "$APP_GROUP/$app"
        echo "\n-------------------------"
        # list the tasks of an app
        curl  "$APP_GROUP/$app"/tasks
    fi
    echo "\n======================="
}

if [[ "$SINGLE_APP" == "" ]]; then
    # run all apps
    for app in $APP_LIST; do
        run_single_app $ACTION $PLATFORM $app
    done
else
    # run the only app
    run_single_app $ACTION $PLATFORM $SINGLE_APP
fi
