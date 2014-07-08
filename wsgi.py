#!/usr/bin/python
import os

repodir = os.environ['OPENSHIFT_REPO_DIR']

virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
try:
    execfile(virtualenv, dict(__file__=virtualenv))
except IOError:
    pass
#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
#

execfile(os.path.join(repodir, "wsgi", "reportmap.wsgi"))
