##!/bin/sh
#
#if [ $(whoami) = root ]; then
#    chown -R randomcoffee:randomcoffee /app
#    su -l randomcoffee /docker-entrypoint.sh "$@"
#    exit $?
#fi
#
#if [ $# != 0 ]; then
#    echo "Executing custom command"
#    exec "$@"
#fi
#uvicorn randomcoffee:app --host 0.0.0.0 --port 8080
