import subprocess
import sys

from octomotron.exc import UserError


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
    print cmd
    if check_call:
        return subprocess.check_call(cmd, shell=True)
    return subprocess.call(cmd, shell=True)


def shell_capture(cmd):
    """
    Run a command and return the output as a string, as though running in
    backticks in bash.
    """
    print cmd
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
    print '%s < %s' % (cmd, data)
    pipe = subprocess.Popen(
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
        except subprocess.CalledProcessError, e:
            sys.exit(1)
    return wrapper
