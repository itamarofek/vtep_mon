import shlex
import time
import os

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils, strutils
from nova.api.validation.parameter_types import mac_address

import subprocess

LOG = logging.getLogger(__name__)

CONF = cfg.CN


def _get_root_helper():
    if CONF.workarounds.disable_rootwrap:
        cmd = 'sudo'
    else:
        cmd = 'sudo /usr/bin/rootwrap %s' % CONF.rootwrap_config
    return cmd

def execute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() method."""
    if 'run_as_root' in kwargs and 'root_helper' not in kwargs:
        kwargs['root_helper'] = _get_root_helper()
    LOG.info(cmd)
    LOG.info(kwargs)
    return processutils.execute(*cmd, **kwargs)


def launch(*cmd, **kwargs):
    shell = kwargs.pop('shell', False)
    if 'run_as_root' in kwargs and 'root_helper' not in kwargs:
        kwargs['root_helper'] = _get_root_helper()
    root_helper = kwargs['root_helper']
    if 'run_as_root' in kwargs and 'root_helper' not in kwargs:
        if shell:
            # root helper has to be injected into the command string
            cmd = [' '.join((root_helper, cmd[0]))] + list(cmd[1:])
        else:
            # root helper has to be tokenized into argument list
            cmd = shlex.split(root_helper) + list(cmd)
    try:
        subprocess.Popen(cmd, shell=shell)
    except OSError as err:
        f = _('Got an OSError\ncommand: %(cmd)r\n'
                   'errno: %(errno)r')
        sanitized_cmd = strutils.mask_password(' '.join(cmd))
        LOG.error(f, {"cmd": sanitized_cmd, "errno": err.errno})
    finally:
        time.sleep(0)


def process_exist(words):
    s = subprocess.Popen(["ps", "ax"], stdout=subprocess.PIPE)
    for x in s.stdout:
        fi = True
        for word in words:
            if word not in x:
                fi = False
                break
        if fi:
            return x.split()[0]
    return False

def get_mac(nic):
    r = execute('cat', '/sys/class/net/%s/address' % nic)
    return r[0].strip()


def device_exists(device):
    """Check if ethernet device exists."""
    return os.path.exists('/sys/class/net/%s' % device)


def netns_exists(name):
    output = execute('ip', 'netns', 'list',
                     run_as_root=True)[0]
    for line in output.split('\n'):
        if name == line.strip():
            return True
    return False

def delete_net_dev(dev):
    """Delete a network device only if it exists."""
    if device_exists(dev):
        execute('ip', 'link', 'delete', dev, run_as_root=True,
                check_exit_code=False)
        LOG.debug("Net device removed: '%s'", dev)

def set_ipaddr(dev_name,address, cidr,mtu = None , up = False):
    """Create a pair of veth devices with the specified names,
    deleting any previous devices with those names."""
    if up:
        execute('ip', 'link', 'set', dev_name, 'up', run_as_root=True)
    execute ('ip', 'addr', 'add', '%s/%s' % (address, cidr),'dev',
              dev_name,run_as_root=True )
    set_device_mtu(dev_name,mtu)


def set_device_mtu(dev, mtu=None):
    """Set the device MTU."""

    if not mtu:
        mtu = CONF.network_device_mtu
    if mtu:
        execute('ip', 'link', 'set', dev, 'mtu',
                mtu, run_as_root=True,
                check_exit_code=[0, 2, 254])

def get_nic_cidr(eth, restart=False):
    ip = None
    show = execute('ip', 'addr', 'show', eth, run_as_root=True)
    for l in show[0].split('\n'):
        if 'inet ' in l:
            for a in l.split(' '):
                if '/' in a:
                    ip = a
    if ip:
        return ip
    if restart:
        execute('ifdown', eth, run_as_root=True)
        execute('ifup', eth, run_as_root=True)
        return get_nic_cidr(eth)
    return None

def set_mac_ip(nic, mac, cidr):
    execute('ip', 'addr', 'flush', 'dev', nic,
            run_as_root=True)
    execute('ip', 'link', 'set', nic, 'address', mac,
            run_as_root=True)
    execute('ip', 'addr', 'add', cidr, 'dev', nic,
            check_exit_code=False,
            run_as_root=True)

def ovsdb_tool(args):
    cmd = ['ovsdb-tool' ] + args
    return execute(*cmd, run_as_root=True)

def ovs_appctl(args):
    cmd = ['ovs-appctl' ] + args
    return execute(*cmd, run_as_root=True)

def vtep_ctl(args):
    bin_path = 'PATH=%s:${PATH}' % os.path.expanduser(CONF.vtep_path)
    cmd = [bin_path, 'vtep-ctl' ] + args    
    return execute(*cmd, run_as_root=True)

def ovs_vtep(args):
    bin_path = 'PATH=%s:${PATH}' % os.path.expanduser(CONF.vtep_path)
    cmd = [bin_path, 'ovs-vtep' ] + args    
    return execute(*cmd, run_as_root=True)

def start_ovs_vtep(ip_list,run_as_deamon=True):
    create_vtep_db()
    vtep_ctl('add-ps','sw1')
    vtep-ctl('set', 'Physical_Switch', 'sw1', 'tunnel_ips='', '.join(ip_list))
    args = ['--log-file=/var/log/openvswitch/ovs-vtep.log', '--pidfile=/var/run/openvswitch/ovs-vtep.pid', 'sw1' ]
    if run_as_deamon:
        args += ['--detach']
    ovs_vtep (args)
    
def create_vtep_db( remove_old=True):
    if remove_old:
        try:
            os.remove(CONF.vtep_db_file)
        except OSError:
            pass    
    ovsdb_tool( 'create', CONF.vtep_db_file, 'CONF.vtep_path' + '/vtep.ovsschema')
    ovs_appctl( '-t', 'ovsdb-server', 'ovsdb-server/add-db', CONF.vtep_db_file)


