#!/bin/bash -x
#based on ubuntu 14.04

OVS_REP0=$HOME/ovs
FROM_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."


cd $HOME && git clone https://github.com/openstack/oslo.rootwrap.git
cd $HOME/oslo.rootwrap && sudo python setup.py install --record /tmp/rootwrap-files.txt
sudo rm -fr `cat /tmp/rootwrap-files.txt` $HOME/oslo.rootwrap/*.egg-info  $HOME/oslo.rootwrap/build
cd $HOME/oslo.rootwrap && sudo python setup.py install

cd $FROM_DIR
sudo python setup.py install --record /tmp/files.txt
sudo rm -fr `cat /tmpfiles.txt` *.egg-info build
sudo python setup.py install


sudo rm -f /etc/init/vtep-mon
sudo cp -r $FROM_DIR/etc/init/* /etc/init

sudo rm -rf /etc/vtep_mon
sudo cp -r $FROM_DIR/etc/vtep_mon /etc

cat $FROM_DIR/etc/vtep_mon/rootwrap.conf | awk '/^exec_dirs/  {$0=$0",'$HOME'/ovs/vtep"} ; {print}' | sudo tee /etc/vtep_mon/rootwrap.conf 
sudo mkdir /var/log/vtep_mon


# clean
if [ "$PREPARE_IMAGE" == "yes" ]; then
   sudo apt-get clean
   sudo rm -f /var/lib/apt/lists/*
   sudo cat /dev/zero > zero
   sudo rm -f zero
fi
