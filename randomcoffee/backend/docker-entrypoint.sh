#!/bin/sh

if [ $(whoami) = root ]; then
    chown -R randomcoffee:randomcoffee /app
    su -l randomcoffee /docker-entrypoint.sh "$@"
    exit $?
fi

if [ $# != 0 ]; then
    echo "Executing custom command"
    exec "$@"
fi

trap 'wait $backend_proc' INT

uvicorn randomcoffee:app --host 0.0.0.0 --port 8080 & backend_proc=$!
# more programs
wait -n $backend_proc # more processes

# trap
