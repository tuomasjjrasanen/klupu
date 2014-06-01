#!/bin/sh

set -eu

if [ $# -ne 2 ]; then
    echo "error: invalid number of arguments $#, expected 2" >&2
    echo "usage: $0 DB_URI KTWEB_DIR" >&2
    exit 1
fi

db_uri=$1
ktweb_dir=$2

this_script_path=$(readlink -e "$0")
this_script_dir=$(dirname "${this_script_path}")

klupung-dbimport-policymakers "${db_uri}" "${this_script_dir}/policymakers.csv"
klupung-dbimport-categories "${db_uri}" "${this_script_dir}/categories.csv"
klupung-dbimport-ktweb "${db_uri}" "${ktweb_dir}"
