import oslo_config

from oslo_log import log as logging

from nova.i18n import _

from vtep_mon.agent import version

cfg = oslo_config.cfg
opts = [
    cfg.MultiOpt('tunnel_ips',item_type=oslo_config.types.IPAddress(version=4),
                  required=False,
                  help="ip list of the vtep switch tunnels"),
    cfg.MultiStrOpt('tunnel_ifs',help="list of vtep nics for tunnel_ips termination end point"),
    cfg.BoolOpt('auto_flood', help='enable default auto_floodind',default = True),
    cfg.BoolOpt('mtu_fragment', help='auto detect importutils', default = False )
]
cfg.CONF.register_cli_opts(opts)
cfg.CONF.import_opt('ovs_vsctl_timeout', 'nova.network.linux_net')

monitor_opts = [
    cfg.StrOpt('fip_device', help=_('name of the detachable data-network device')),
    cfg.StrOpt('phy_interface', default='tap0',
                 help=_('name of the psuedo phyiscal interface.')),
    cfg.StrOpt('switch', default='br-vtep@HOSTIP',
                 help=_('name of the vtep ovs switch.')),
    cfg.StrOpt('vtep_db_file', default='/etc/openvswitch/vtep.db',
                help=_('path to the vtep_db_file')),
    cfg.StrOpt('vtep_path',help=_('path to the ovs-vtep executable'))

]

cfg.CONF.register_opts(monitor_opts, 'monitor')

agent_opts = [
	cfg.StrOpt('root_helper',help='name of the run as root command')
]

cfg.CONF.register_opts(agent_opts, 'agent')

LOG = logging.getLogger(__name__)

# import the configuration options
# cfg.CONF.set_default('rootwrap_config', '/etc/vtep_mon/rootwrap.conf')

def init(args, **kwargs):
    product_name = "vtep_mon"
    logging.register_options(cfg.CONF)
    logging.setup(cfg.CONF, product_name)
    cfg.CONF(args=args, project=product_name,
             version='%%(prog)s %s' % version.version_info.release_string(),
             **kwargs)
    
def get_root_helper(conf):
    return conf.AGENT.root_helper
