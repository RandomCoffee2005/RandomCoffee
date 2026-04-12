#!/bin/sh

if [ $(whoami) = root ]; then
    # Monday 00:00: run weekly pairing generation.
    cat > /etc/crontabs/randomcoffee <<'EOF'
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 0 * * 1 /usr/local/bin/python -m pairalgo >>/proc/1/fd/1 2>>/proc/1/fd/2
EOF
    chown randomcoffee:randomcoffee /etc/crontabs/randomcoffee
    chmod 600 /etc/crontabs/randomcoffee

    chown -R randomcoffee:randomcoffee /app
    su randomcoffee /docker-entrypoint.sh "$@"
    exit $?
fi

if [ $# != 0 ]; then
    echo "Executing custom command"
    exec "$@"
fi

trap 'kill "$backend_proc" "$cron_proc" 2>/dev/null; wait "$backend_proc" "$cron_proc" 2>/dev/null' INT TERM

crond -f -l 8 & cron_proc=$!

uvicorn randomcoffee:app --host 0.0.0.0 --port 8080 & backend_proc=$!
# more programs
wait -n $backend_proc $cron_proc # more processes

kill "$backend_proc" "$cron_proc" 2>/dev/null
wait "$backend_proc" "$cron_proc" 2>/dev/null

# trap
