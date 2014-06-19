#!/bin/bash

set -eu

usage_error()
{
    echo "error: $1" >&2
    echo "Try '$0 --help' for more information". >&2
    return 1
}

while [ $# -gt 0 ]; do
    case $1 in
        -h|--help)
            shift
            echo "Usage: $0"
            echo
            echo "Start server."
            echo
            echo "Options:"
            echo "    -h, --help                   print help and exit"
            echo
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            usage_error "invalid argument '$1'"
            ;;
        *)
            break
            ;;
    esac
done
        
if [ $# -ne 0 ]; then
    usage_error "invalid number of arguments ($#), expected 0"
fi

G_dbpath=$(readlink -f klupung.db)
G_dburi="sqlite:///${G_dbpath}"

gunicorn \
    --env KLUPUNG_DB_URI="${KLUPUNG_DB_URI:-${G_dburi}}" \
    --workers 2 \
    --bind "${KLUPUNG_API_ADDRESS:-localhost}:${KLUPUNG_API_PORT:-8080}" \
    --daemon \
    --error-logfile error.log \
    --access-logfile acces.log \
    --pid klupung.pid \
    klupung.flask.wsgi:app
