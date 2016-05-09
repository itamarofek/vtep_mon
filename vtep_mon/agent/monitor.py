#!/usr/bin/env python

import os

import sys

import time

from vtep_mon.common import config

from oslo_log import log as logging

from oslo_utils import importutils

from nova.i18n import _LI

from vtep_mon.common import utils

LOG = logging.getLogger(__name__)


class MonitorCallback(object):

    def __init__(self):
        pass
    def check_vtep(self):
        """check the vtep status"""
        pass                
    def start_vtep(self, device, vtep_data_ip):
        """perform all start up procedures initialize empty db."""
        return self.client.call(self.context, 'get_vif_for_provider_ip',
                                provider_ip=provider_ip)

    def stop_vtep(self):
        pass



class VtepMonitor(object):

    def __init__(self,cfg,tunnel_ips,routbale_device = None):
        super(VtepMonitor, self).__init__()
        self.tunnel_ips = tunnel_ips
        self.routbale_device = routbale_device
        self.cfg = cfg
        self.__set_switch_name()
        print ("tunnel_ips = %s,switch name = %s" %(self.tunnel_ips,self.sw_name))

    def __set_switch_name(self):
        if '@' in self.cfg.CONF.monitor.switch:
            name = self.cfg.CONF.monitor.switch.split('@')
            if len(name) == 2 and name [1] == 'HOSTIP':
                self.sw_name = "%s@%s" % ( name[0] , self.tunnel_ips[0])
                return
        self.sw_name = self.cfg.CONF.monitor.switch

    def __initialze_db(self):
	empty_db_path = self.get_empty_db_path()
        if False == os.path.isfile(empty_db_path):
            utils.create_empty_vtep_db(self.cfg.CONF.monitor.vtep_db_file,
                                       empty_db_path,
                                       self.cfg.CONF.monitor.vtep_path,
                                       self.sw_name)
	else:
            utils.create_vtep_db(self.cfg.CONF.monitor.vtep_db_file,
                                 empty_db_path,
                                 self.cfg.CONF.monitor.vtep_path)


    def get_empty_db_path(self):
        return "%s/%s.db" %(os.path.dirname(self.cfg.CONF.monitor.vtep_db_file),
                            self.sw_name)


    def __create_bridge(self):
        utils.add_ovs_bridge(self.sw_name)


    def start_vtep_device(self):
        utils.add_to_exe_path(self.cfg.CONF.monitor.vtep_path)
        self.__initialze_db()
        if not utils.device_exists(self.cfg.CONF.monitor.phy_interface):
            utils.create_tap_device(self.cfg.CONF.monitor.phy_interface)
            utils.ifup_down(self.cfg.CONF.monitor.phy_interface)
        self.__create_bridge()
        utils.add_port_to_bridge(self.sw_name,self.cfg.CONF.monitor.phy_interface)
        if self.routbale_device:
            utils.ifup_down(self.routbale_device)
        utils.start_ovs_vtep(self.sw_name,self.tunnel_ips,
			     True,
                             self.cfg.CONF.auto_flood,
                             self.cfg.CONF.mtu_fragment)

def main():
    config.init(sys.argv[1:])
    tunnel_ips = list()
    if config.cfg.CONF.tunnel_ifs:
        tunnel_ips = utils.get_interfaces_ips(config.cfg.CONF.tunnel_ifs)
    else:
        tunnel_ips = config.cfg.CONF.tunnel_ips
    agent = VtepMonitor(config.cfg,tunnel_ips,config.cfg.CONF.monitor.fip_device)
    # Start everything.
    agent.start_vtep_device()
    LOG.info(_LI("Agent initialized successfully, now running. "))

if __name__ == "__main__":
    main()
