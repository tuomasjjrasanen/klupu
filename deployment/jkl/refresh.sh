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
            echo "Refresh database."
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

G_this_script_path=$(readlink -e "$0")
G_this_script_dir=$(dirname "${G_this_script_path}")

# Download failure is not fatal. jyvaskyla.fi might be down for example,
# just keep going because we might have just downloaded at least some
# new documents.
echo "Downloading new documents..."
"${G_this_script_dir}/download.sh" || true

echo "Stopping klupung..."
"${G_this_script_dir}/stop.sh" || {
    # Stop failure is fatal, but try to start the service before dying.
    echo "Starting klupung..."
    "${G_this_script_dir}/start.sh"
    exit 1
}

echo "Importing documents into db..."
"${G_this_script_dir}/dbimport.sh" || true

echo "Starting klupung..."
"${G_this_script_dir}/start.sh"
