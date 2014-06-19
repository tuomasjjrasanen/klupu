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
            echo "Download documents."
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

klupung-download-ktweb \
    --min-request-interval 0.2 \
    "${G_this_script_dir}/current_ktweb_urls.txt" .

if [ -d paatokset/pela/ ]; then
    # pela seems to be a mistyped name of pelajk, move all stuff to
    # pelajk and get rid of pela since it is not an official
    # abbreviation and hence missing from the DB (and policymakers.csv)
    rsync -aP paatokset/pela/ paatokset/pelajk/
    rm -rf paatokset/pela/
fi

if [ -d paatokset/tarkjkl/ ]; then
    # Some of the meeting documents of tarkltk in Spring 2013 are
    # archived under tarkjkl alias, which is not an official
    # abbreviation, hence all tarkjkl-stuff is moved under tarkltk
    rsync -aP paatokset/tarkjkl/ paatokset/tarkltk/
    rm -rf paatokset/tarkjkl/
fi

klupung-geocode-ktweb paatokset Jyväskylä
