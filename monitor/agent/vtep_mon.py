import os

from oslo_config import cfg

from oslo_log import log as logging

from oslo_utils import importutils

from monitor.common import config

from nova.i18n import _LI

import sys

LOG = logging.getLogger(__name__)


opts = [
    cfg.IPOpt('data_ip', required=True,
               help="ip of the vtep switch")
]


CONF.register_opts(opts)


class MonitorCallback(object):

    def __init__(self):
        self.client = rpc.get_client(target)
        self.context = context.get_admin_context()
        super(HyperAgentCallback, self).__init__()

    def check_vtep(self):
        """check the vtep status"""

    def start_vtep(self, device, vtep_data_ip):
        """perform all start up procedures initialize empty db."""
        return self.client.call(self.context, 'get_vif_for_provider_ip',
                                provider_ip=provider_ip)

    def stop_vtep(self):



class VtepMonitor(object):

    def __init__(self):
        super(VtepMonitor, self).__init__()
        self.instance_id = cfg.CONF.host


        self.call_back = MonitorCallback()
        self.server.start()

    def execute(self):


def main():
    config.init(sys.argv[1:])

    agent = VtepMonitor()
    # Start everything.
    LOG.info(_LI("Agent initialized successfully, now running. "))
    agent.daemon_loop()


if __name__ == "__main__":
    main()
