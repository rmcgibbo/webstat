from fabric.api import *
env.hosts = ['vsp-compute']

def deploy():
    with cd('webstat'):
        run('git pull')
        run('python scripts/cluster_daemon.py')

def coffee():
    local('coffee -c webstat/assets/main.coffee')
