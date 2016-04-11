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
        print ("tunnel_ips = %s,routbale_device = %s" %(self.tunnel_ips,self.routbale_device))

    def __initialze_db(self):
        utils.create_vtep_db(self.cfg.CONF.monitor.vtep_db_file,self.cfg.CONF.monitor.vtep_path)

    def __create_bridge(self):
        utils.add_ovs_bridge(self.cfg.CONF.monitor.switch)


    def start_vtep_device(self):
        utils.add_to_exe_path(self.cfg.CONF.monitor.vtep_path)
        self.__initialze_db()
        if not utils.device_exists(self.cfg.CONF.monitor.phy_interface):
            utils.create_tap_device(self.cfg.CONF.monitor.phy_interface)
            utils.ifup_down(self.cfg.CONF.monitor.phy_interface)
        self.__create_bridge()
        utils.add_port_to_bridge(self.cfg.CONF.monitor.switch,self.cfg.CONF.monitor.phy_interface)
        if self.routbale_device:
            utils.ifup_down(self.routbale_device)
        utils.start_ovs_vtep(self.cfg.CONF.monitor.switch,self.tunnel_ips)

def main():
    config.init(sys.argv[1:])
    print config.cfg.CONF.tunnel_ips
    #import pdb
    #pdb.set_trace()
    agent = VtepMonitor(config.cfg,config.cfg.CONF.tunnel_ips,config.cfg.CONF.monitor.fip_device)
    # Start everything.
    agent.start_vtep_device()
    LOG.info(_LI("Agent initialized successfully, now running. "))

if __name__ == "__main__":
    main()
