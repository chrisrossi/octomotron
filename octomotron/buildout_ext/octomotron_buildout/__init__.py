import os


def extension(buildout):
    buildout = buildout['buildout']
    buildout_dir = buildout['directory']
    srcdir = os.path.join(buildout_dir, 'src')
    develop = []
    for fname in os.listdir(srcdir):
        if fname.startswith('.'):
            continue
        develop.append(os.path.join(srcdir, fname))
    buildout['develop'] = '\n'.join(develop)
