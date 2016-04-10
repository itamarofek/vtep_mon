#!/bin/bash -x

# based on ubuntu 14.04.03




FROM_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
PYTHON_PKG_DIR=/usr/lib/python2.7/dist-packages

bin_files='vtep-mon'

mkdir /var/log/vtep_mon


# clean
apt-get clean
rm -f /var/lib/apt/lists/*
cat /dev/zero > zero
rm -f zero

