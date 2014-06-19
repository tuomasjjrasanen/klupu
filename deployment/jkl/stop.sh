#!/bin/sh

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
            echo "Stop server."
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

if [ -f klupung.pid ]; then
    klupung_pid=$(cat klupung.pid)
    kill -0 "${klupung_pid}" || exit 0
    kill "${klupung_pid}"
    kill_time=$(date +%s)
    while kill -0 "${klupung_pid}"; do
        time_now=$(date +%s)
        if [ $((time_now - kill_time)) -ge 5 ]; then
            break
        fi
        sleep 0.5
    done
    kill -9 "${klupung_pid}"
fi
