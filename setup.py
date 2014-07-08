from setuptools import setup

setup(name='Remotemap',
      version='0.2',
      description='OpenShift App',
      author='Cristian Consonni',
      author_email='kikkocristian@gmail.com',
      url='http://www.python.org/sigs/distutils-sig/',
      install_requires=open('requirements.txt').readlines(),
      )
