from fabric.api import *
env.hosts = ['vsp-compute']

def deploy():
    "Start the daemon on the remote pbs servers"

    with cd('webstat'):
        run('git pull')
        run('python scripts/cluster_daemon.py')

def coffee():
    "Compile the coffeescript to static javascript"
    local('coffee -c -o webstat/static/ webstat/assets/main.coffee')
