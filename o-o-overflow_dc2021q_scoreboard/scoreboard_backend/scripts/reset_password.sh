#!/bin/sh

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <email> <password>"
    exit -1
fi

if [ -z ${STAGE+x} ]; then
    stage="development"
else
    stage=$STAGE
fi

sls invoke -f user_reset_password -d "{\"email\": \"$1\", \"password\": \"$2\"}" -l --stage $stage
exit 0;
