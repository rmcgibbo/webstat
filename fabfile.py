from fabric.api import *
env.hosts = ['vsp-compute']

def deploy():
    run('cd webstat')
    run('git pull')
    run('python cluster_daemon.py')

def coffee():
    local('coffee -c webstat/assets/main.coffee')
