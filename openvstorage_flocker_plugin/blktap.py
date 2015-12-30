'''
Copyright 2015 iNuron NV.  All rights reserved.
Licensed under the Apache v2 License.
'''
import os
import subprocess

__author__ = "Chrysostomos Nanakos"
__copyright__ = "Copyright 2015, iNuron NV"
__version__ = "0.1"
__maintainer__ = "Chrysostomos Nanakos"
__email__ = "cnanakos@openvstorage.com"
__status__ = "Development"


def cmd_open(cmd, bufsize=-1, env=None):
    inst = subprocess.Popen(cmd, shell=False, bufsize=bufsize,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, close_fds=True)
    return inst


def doexec(args, inputtext=None):
    proc = cmd_open(args)
    if inputtext is not None:
        proc.stdin.write(inputtext)
    stdout = proc.stdout
    stderr = proc.stderr
    rc = proc.wait()
    return (rc, stdout, stderr)


class TDFlags:
    TD_DEAD = 0x0001
    TD_CLOSED = 0x0002
    TD_QUIESCE_REQUESTED = 0x0004
    TD_QUIESCED = 0x0008
    TD_PAUSE_REQUESTED = 0x0010
    TD_PAUSED = 0x0020
    TD_SHUTDOWN_REQUESTED = 0x0040
    TD_LOCKING = 0x0080
    TD_LOG_DROPPED = 0x0100
    TD_PAUSE_MASK = TD_PAUSE_REQUESTED | TD_PAUSED


class TapdiskException(Exception):
    pass


class Tapdisk(object):
    '''Tapdisk operations'''
    TAP_CTL = 'tap-ctl'
    TAP_DEV = '/dev/xen/blktap-2/tapdev'

    class TapdiskInt(object):
        def __init__(self, pid=None, minor=-1, state=None, volume=None,
                     device=None, driver=None):
            self.pid = pid
            self.minor = minor
            self.state = state
            self.volume = volume
            self.device = device
            self.driver = driver

        def __str__(self):
            return 'volume=%s pid=%s minor=%s state=%s device=%s ' \
                   % (self.volume, self.pid, self.minor, self.state,
                      self.device)

    @staticmethod
    def exc(*args):
        rc, stdout, stderr = doexec([Tapdisk.TAP_CTL] + list(args))
        out, err = stdout.read().strip(), stderr.read().strip()
        stdout.close()
        stderr.close()
        if rc:
            raise TapdiskException('%s failed (%s %s %s)' %
                                   (args, rc, out, err))
        return out

    @staticmethod
    def check():
        try:
            Tapdisk.exc('check')
            return 0
        except Exception, e:
            print "'tap-ctl check' failed: %s" % e
            return -1

    @staticmethod  # NOQA
    def list():
        tapdisks = []
        _list = Tapdisk.exc('list')
        if not _list:
            return []

        for line in _list.split('\n'):
            tapdisk = Tapdisk.TapdiskInt()

            for pair in line.split():
                key, value = pair.split('=', 1)
                if key == 'pid':
                    tapdisk.pid = value
                elif key == 'minor':
                    tapdisk.minor = int(value)
                    if tapdisk.minor >= 0:
                        tapdisk.device = '%s%s' % \
                            (Tapdisk.TAP_DEV, tapdisk.minor)
                elif key == 'state':
                    tapdisk.state = int(value, 16)
                elif key == 'args' and value.find(':') != -1:
                    args = value.split(':')
                    tapdisk.driver = args[0]
                    tapdisk.volume = args[1]

            if tapdisk.driver == "openvstorage":
                tapdisks.append(tapdisk)

        return tapdisks

    @staticmethod
    def fromDevice(device):
        if device.startswith(Tapdisk.TAP_DEV):
            minor = os.minor(os.stat(device).st_rdev)
            tapdisks = filter(lambda x: x.minor == minor, Tapdisk.list())
            if len(tapdisks) == 1:
                return tapdisks[0]
        return None

    @staticmethod
    def create(volume, readonly=False):
        uri = "%s:%s" % ('openvstorage', volume)

        if readonly:
            return Tapdisk.exc('create', "-a%s" % uri, '-R')
        else:
            return Tapdisk.exc('create', "-a%s" % uri)

    @staticmethod
    def destroy(device):
        tapdisk = Tapdisk.fromDevice(device)
        if tapdisk:
            if tapdisk.pid:
                Tapdisk.exc('destroy',
                            '-p%s' % tapdisk.pid,
                            '-m%s' % tapdisk.minor)
            else:
                Tapdisk.exc('free', '-m%s' % tapdisk.minor)

    @staticmethod
    def pause(device):
        tapdisk = Tapdisk.fromDevice(device)
        if tapdisk and tapdisk.pid:
            Tapdisk.exc('pause',
                        '-p%s' % tapdisk.pid,
                        '-m%s' % tapdisk.minor)

    @staticmethod
    def unpause(device):
        tapdisk = Tapdisk.fromDevice(device)
        if tapdisk and tapdisk.pid:
            Tapdisk.exc('unpause',
                        '-p%s' % tapdisk.pid,
                        '-m%s' % tapdisk.minor)

    @staticmethod
    def stats(device):
        tapdisk = Tapdisk.fromDevice(device)
        if tapdisk and tapdisk.pid:
            import json
            stats = Tapdisk.exc('stats',
                                '-p%s' % tapdisk.pid,
                                '-m%s' % tapdisk.minor)
            return json.loads(stats)
        return None

    @staticmethod
    def busy_pid(device):
        rc, stdout, stderr = doexec(['fuser', device])
        out = stdout.read().strip()
        stderr.close()
        stdout.close()
        return out

    @staticmethod
    def is_mounted(device):
        fd = open("/proc/mounts", "r")
        for line in fd.readlines():
            if device == line.split()[0]:
                return True
        fd.close()
        return False

    @staticmethod
    def is_paused(device):
        tapdisk = Tapdisk.fromDevice(device)
        if tapdisk:
            return not not (tapdisk.state & TDFlags.TD_PAUSED)
        return None

    @staticmethod
    def is_running(device):
        tapdisk = Tapdisk.fromDevice(device)
        if tapdisk:
            return not (tapdisk.state & TDFlags.TD_PAUSE_MASK)
        return None

    @staticmethod
    def query_state(device):
        tapdisk = Tapdisk.fromDevice(device)
        if tapdisk:
            if tapdisk.state & TDFlags.TD_PAUSED:
                return "paused"
            if tapdisk.state & TDFlags.TD_PAUSE_REQUESTED:
                return "pausing"
            return "running"
