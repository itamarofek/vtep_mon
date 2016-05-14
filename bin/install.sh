#!/bin/bash -x

# based on ubuntu 14.04.03

exec_dirs


OVS_REP0=$HOME/ovs
FROM_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
PYTHON_PKG_DIR=/usr/lib/python2.7/dist-packages

sudo python setup.py install --record /tmp/files.txt
cat /tmpfiles.txt |xargs sudo rm -rf
sudo python setup.py install


sudo rm -f /etc/init/vtep-mon
sudo cp -r $FROM_DIR/etc/init/* /etc/init

rm -rf /etc/vtep_mon
sudo cp -r $FROM_DIR/etc/vtep_mon /etc

cat $FROM_DIR/etc/vtep_mon/rootwrap.conf | awk '/^exec_dirs/  {$0=$0",$HOME/ovs/vtep"} ; {print}' > /etc/vtep_mon/rootwrap.conf 






mkdir /var/log/vtep_mon


# clean
sudo apt-get clean
sudo rm -f /var/lib/apt/lists/*
sudo cat /dev/zero > zero
sudo rm -f zero

