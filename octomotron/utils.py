import logging
import os
import subprocess
import sys

from octomotron.exc import UserError

log = logging.getLogger(__name__)


def unique_int(start, other_values):
    if other_values:
        while start in other_values:
            start += 1
    return start


def get_build(args):
    name = args.build
    builds = args.harness.builds
    if name:
        build = builds.get(name)
        if not build:
            raise UserError('No such build: %s' % name)
    elif len(builds) == 1:
        build = builds.values()[0]
    else:
        raise UserError('Must specify build.')

    return build


def shell(cmd, check_call=True):
    """
    Run a command as though it were being called from a shell script.
    """
    log.info(cmd)
    if check_call:
        return subprocess.check_call(cmd, shell=True)
    return subprocess.call(cmd, shell=True)


def shell_capture(cmd):
    """
    Run a command and return the output as a string, as though running in
    backticks in bash.
    """
    log.info(cmd)
    output = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
    return output


def shell_pipe(cmd, data):
    """
    Run a command and return the it's input as a writable file object, for
    piping data to.
    """
    if len(data) < 100:
        logdata = data
    else:
        logdata = '[data]'
    log.info('%s < %s', cmd, logdata)
    subprocess.Popen(
        cmd, shell=True, stdin=subprocess.PIPE).communicate(data)


def shell_script(f):
    """
    Used as decorator for function that will be calling out to the shell.
    Catches subprocess.CalledProcessError and exits. The subprocess is relied
    upon to report its own error message.
    """
    def wrapper(*args, **kw):
        try:
            return f(*args, **kw)
        except subprocess.CalledProcessError:
            sys.exit(1)
    return wrapper


def only_one(name):
    """
    Decorator used to make sure a particular operation can only run once
    globally on the same machine.  Useful for setting tight intervals via cron
    and not having to worry whether one run finishes before the next run.  If
    the operation is already running, we just exit.
    """
    def decorator(f):
        def wrapper(args):
            pids = args.harness.pids
            if not os.path.exists(pids):
                os.makedirs(pids)
            pidfile = os.path.join(pids, name)
            if os.path.exists(pidfile):
                # pid file exists
                # If using a sane operating system with procfs, we check to see
                # whether process is still actually running.
                log = logging.getLogger(name)
                is_running = True
                pid = open(pidfile).read().strip()
                if os.path.exists('/proc'):
                    is_running = os.path.exists(os.path.join('/proc', pid))
                if is_running:
                    log.warn("%s already running with pid %s" % (name, pid))
                    log.warn("Exiting.")
                    sys.exit(1)
                else:
                    log.warn("Found stale pid file for %s (pid %s)." %
                             (name, pid))
            with open(pidfile, 'w') as out:
                print >> out, str(os.getpid())

            try:
                return f(args)
            finally:
                os.remove(pidfile)

        return wrapper
    return decorator

