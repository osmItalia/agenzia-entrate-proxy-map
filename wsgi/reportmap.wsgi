#!/usr/bin/python
import os
import sys

repodir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.dirname(__file__) or '.')
try:
    if os.path.exists(os.path.join(os.environ['OPENSHIFT_HOMEDIR'], "python-2.6")):
        PY_DIR = os.path.join(os.environ['OPENSHIFT_HOMEDIR'], "python-2.6")
    else:
        PY_DIR = os.path.join(os.environ['OPENSHIFT_HOMEDIR'], "python")
except KeyError:
    PY_DIR = os.environ['OPENSHIFT_HOMEDIR']

virtenv = PY_DIR + '/virtenv/'

PY_CACHE = os.path.join(virtenv, 'lib', '2.6', 'site-packages')

os.environ['PYTHON_EGG_CACHE'] = os.path.join(PY_CACHE)
virtualenv = os.path.join(virtenv, 'bin/activate_this.py')

try:
    execfile(virtualenv, dict(__file__=virtualenv))
except IOError:
    pass

# Change working directory so relative paths (and template lookup) work again
reportmap_dir = os.path.join(repodir, 'wsgi', 'reportmap')
sys.path.append(reportmap_dir)
os.chdir(reportmap_dir)


from reportmap import app as application
