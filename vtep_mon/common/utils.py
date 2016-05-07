import shlex
import time
import os
import re

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils, strutils
from nova.api.validation.parameter_types import mac_address

import subprocess

LOG = logging.getLogger(__name__)

CONF = cfg.CONF


def _get_root_helper():
    if CONF.workarounds.disable_rootwrap:
        cmd = 'sudo'
    else:
        cmd = 'sudo /usr/bin/rootwrap %s' % CONF.rootwrap_config
    return cmd

def add_to_exe_path(path, as_prefix=True):
    if as_prefix:
        os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
    else:
        os.environ["PATH"] += os.pathsep + path

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

def kill_pid(pid)
    execute('kill', pid)
    
def process_exist(proc_name):
    ps = subprocess.Popen("ps ax -o pid= -o args= ", shell=True, stdout=subprocess.PIPE)
    ps_pid = ps.pid
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()

    for line in output.split("\n"):
        res = re.findall("(\d+) (.*)", line)
        if res:
            pid = int(res[0][0])
            if proc_name in res[0][1] and pid != os.getpid() and pid != ps_pid:
                return pid
    return None

def create_tap_device(device):
    execute( 'ip' ,'tuntap', 'add', 'dev',device, 'mode', 'tap', run_as_root=True)

def add_port_to_bridge(bridge,port, replace = True):
    if replace:
        ovs_vsctl(['--if-exists', 'del-port', bridge, port])
    ovs_vsctl(['--may-exist','add-port', bridge, port])


def get_mac(nic):
    executer = execute('cat', '/sys/class/net/%s/address' % nic)
    return r[0].strip()


def device_exists(device):
    """Check if ethernet device exists."""
    return os.path.exists('/sys/class/net/%s' % device)


def ifup_down(device, up = True):
    if device_exists(device):
        if up:
            execute('ifup',device,run_as_root=True)
        else:
            execute('ifdown',device,run_as_root=True)
        return True
    else:
        return False
 
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
        return ip.split('/')
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

def ovs_vsctl(args):
    full_args = ['ovs-vsctl', '--timeout=%s' % CONF.ovs_vsctl_timeout] + args
    return execute(*full_args, run_as_root=True)

def add_ovs_bridge(br_name):
    ovs_vsctl(['--may-exist', 'add-br', br_name])

def ovs_appctl(args):
    cmd = ['ovs-appctl'] + args
    return execute(*cmd, run_as_root=True)

def vtep_ctl(args):
    print args
    cmd = ['vtep-ctl'] + args
    return execute(*cmd, run_as_root=True)

def ovs_vtep(args):
    cmd = ['ovs-vtep'] + args
    return execute(*cmd, run_as_root=True)

def start_ovs_vtep(switch,ip_list,run_as_deamon=True,mtu_fragment=False):
    vtep_ctl(['set', 'Physical_Switch', switch, 'tunnel_ips=%s' % ",".join(ip_list)])
    args = ['--log-file=/var/log/openvswitch/ovs-vtep.log',
            '--pidfile=/var/run/openvswitch/ovs-vtep.pid', switch ]
    if auto_flood:
        args += ['--auto_flood']
    if not mtu_fragment:
         args += ['--fragment']
    if run_as_deamon:
        args += ['--detach']
    ovs_vtep (args)

def create_empty_vtep_db(db_file, switch_name):
    ovsdb_tool(['create', db_file,vtep_path + '/vtep.ovsschema'])
    ovs_dir = os.path.dirname(db_file)
    execute('OVS_RUNDIR=%s' % ovs_dir, 'OVS_LOGDIR=%s' % ovs_dir,
            'OVS_DBDIR=%s'  % ovs_dir, 'OVS_SYSCONFDIR=%s' % ovs_dir,
            'OVS_PKGDATADIR=%s' % ovs_dir, 'ovsdb-server',
            '--detach', '--no-chdir' ,'--pidfile=%s/pid' % os_dir,
            '--remote=ptcp:54999' '--unixctl=%s/unixctl' %ovs_dir, db_file )
    vtep_ctl( ['--timeout=5', '-vreconnect:emer', '--db=tcp:127.0.0.1:54999',
              'add-ps', switch_name])
    ovs_pid = None
    with open('%s/pid' % os_dir, 'r') as infile:
        ovs_pid = infile.readline()
        kill_pid(ovs_pid)



def create_vtep_db(db_file,empty_vtep_db,vtep_path,port=6640,remove_old=True):
    if remove_old:service', 'openvswitch-switch', 'stop
        try:
            pid = process_exist('ovs-vtep')
            if pid :
                execute('kill', '-HUP', pid, run_as_root=True )
            execute('service', 'openvswitch-switch', 'stop', run_as_root=True)
            time.sleep(1)
            os.remove(db_file)
            execute('service', 'openvswitch-switch', 'start',run_as_root=True)
        except OSError:
            pass
    execute( 'cp', empty_vtep_db, db_file )
    ovs_appctl([ '-t', 'ovsdb-server', 'ovsdb-server/add-db',
            db_file ])
    ovs_appctl(['-t', 'ovsdb-server', 'ovsdb-server/add-remote',
               'ptcp:%s' % port])


def get_interfaces_ips( interface_list):
    if not interface_list:
        return None
    ip_list = list()
    for if_device in interface_list:
            ip_list.insert(get_nic_cidr(if_device)[0])
    return ip_list
