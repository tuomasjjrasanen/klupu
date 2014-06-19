#!/bin/bash

set -eu

virtualenv env
source env/bin/activate
pip install -r requirements.txt
git init
