#!/bin/bash

commit="$1"
date="$2"
name="$3"
email="$4"

git filter-branch --env-filter \
    "if [ \$GIT_COMMIT = '$commit' ]; then
         export GIT_AUTHOR_DATE='$date'
         export GIT_AUTHOR_NAME='$name'
         export GIT_AUTHOR_EMAIL='$email'
         export GIT_COMMITTER_DATE='$date'
         export GIT_COMMITTER_NAME='$name'
         export GIT_COMMITTER_EMAIL='$email'
     fi"
