#!/bin/sh

set -eu

if [ $# -ne 1 ]; then
    echo "error: invalid number of arguments $#, expected 1" >&2
    echo "usage: $0 DOWNLOAD_DIR" >&2
    exit 1
fi

download_dir=$1

this_script_path=$(readlink -e "$0")
this_script_dir=$(dirname "${this_script_path}")

klupung-download-ktweb "${this_script_dir}/ktweb_urls.txt" "${download_dir}"

# pela seems to be a mistyped name of pelajk, move all stuff to pelajk
# and get rid of pela since it is not an official abbreviation and hence
# missing from the DB (and policymakers.csv)
rsync -aP "${download_dir}/paatokset/pela/" "${download_dir}/paatokset/pelajk/"
rm -rf "${download_dir}/paatokset/pela/"

# Some of the meeting documents of tarkltk in Spring 2013 are archived
# under tarkjkl alias, which is not an official abbreviation, hence all
# tarkjkl-stuff is moved under tarkltk
rsync -aP "${download_dir}/paatokset/tarkjkl/" "${download_dir}/paatokset/tarkltk/"
rm -rf "${download_dir}/paatokset/tarkjkl/"
