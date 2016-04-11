# vtep_mon
BGW installation

add-apt-repository -y cloud-archive:liberty

apt-get update && apt-get upgrade

apt-get install git

apt-get install openvswitch-switch python-openvswitch

apt-get install python-oslo.config python-oslo.messaging python-oslo.rootwrap

apt-get install  nova-api nova-api-os-compute

git clone https://github.com/itamarofek/vtep_mon

git clone https://github.com/itamarofek/ovs

ovsdb-tool create /etc/openvswitch/vtep.db /home/ubuntu/ovs/vtep/vtep.ovsschema

ovs-appctl -t ovsdb-server ovsdb-server/add-db /etc/openvswitch/vtep.db

export PATH=/home/ubuntu/ovs/vtep:$PATH

vtep-ctl add-ps vpc_ps_name

vtep-ctl set Physical_Switch vpc1 tunnel_ips=provider_ip,routable_ip 
