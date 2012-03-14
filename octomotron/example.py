import os
import pkg_resources
import shutil


def config_parser(name, subparsers):
    parser = subparsers.add_parser(name, help='Spit out an example.')
    subsub = parser.add_subparsers(title='subcommand',
                                   help='Available subcommands')
    list_parser = subsub.add_parser('list', help='List available examples')
    list_parser.set_defaults(func=list_examples, parser=list_parser)

    create_parser = subsub.add_parser('create', help='Spit out an example.')
    create_parser.add_argument('--unsafe', action='store_true', default=False,
                       help='Agree to overwrite existing files.')
    create_parser.add_argument('name', help='Name of example to create.')
    create_parser.add_argument('target', help='Target directory for example.')
    create_parser.set_defaults(func=main, parser=create_parser)


def list_examples(args):
    for name in pkg_resources.resource_listdir('octomotron', 'examples'):
        print name


def main(args):
    target = os.path.abspath(args.target)
    if not args.unsafe and os.path.exists(target):
        args.parser.error("Target exists. Use --unsafe to overwrite.")

    parent = os.path.dirname(target)
    if not os.path.exists(parent):
        args.parser.error("No such directory: %s" % parent)

    src = 'examples/%s' % args.name
    if not pkg_resources.resource_exists('octomotron', src):
        args.parser.error("No such example: %s" % args.name)

    if not os.path.exists(target):
        os.mkdir(target)
    copytree(src, target)


def copytree(src, target):
    for fname in pkg_resources.resource_listdir('octomotron', src):
        child_src = '/'.join((src, fname))
        child_target = os.path.join(target, fname)
        if pkg_resources.resource_isdir('octomotron', child_src):
            if not os.path.exists(child_target):
                os.mkdir(child_target)
            copytree(child_src, child_target)
        else:
            copyfile(child_src, child_target)

def copyfile(src, target):
    with pkg_resources.resource_stream('octomotron', src) as src_stream:
        with open(target, 'wb') as target_stream:
            shutil.copyfileobj(src_stream, target_stream)
