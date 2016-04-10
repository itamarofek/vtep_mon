from oslo_config import cfg

from oslo_log import log as logging

from nova.i18n import _

from monitor import version



LOG = logging.getLogger(__name__)

# import the configuration options
cfg.CONF.set_default('rootwrap_config', '/etc/vtep_mon/rootwrap.conf')

def init(args, **kwargs):
    product_name = "vtep_mon"
    logging.register_options(cfg.CONF)
    logging.setup(cfg.CONF, product_name)
    cfg.CONF(args=args, project=product_name,
             version='%%(prog)s %s' % version.version_info.release_string(),
             **kwargs)


def get_root_helper(conf):
    return conf.AGENT.root_helper
