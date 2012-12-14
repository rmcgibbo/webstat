from fabric.api import *


env.roledefs = {'daemon': ['vsp-compute', 'certainty-b'],
                'certainty-queue': ['vspm10'],
                'server': ['vspm42-ubuntu'],
                }

def prepare_deploy():
    local("git add -p && git commit")
    local("git push")

@roles('daemon')
def run_daemon():
    "Start the daemon on the remote pbs servers"
    with cd('webstat'):
        run('git pull')
        run('python scripts/cluster_daemon.py daemon')

@roles('server')
def run_server():
    with cd('webstat'):
        run('git pull')
        run('supervisorctl stop webstat')
        run('supervisorctl start webstat')

@roles('certainty-queue')
def run_certainty_queue():
    with cd('webstat'):
        run('git pull')
        run('python scripts/certainty_queue.py')

def deploy():
    prepare_deploy()

    #http://docs.fabfile.org/en/1.5/usage/execution.html#intelligently-executing-tasks-with-execute
    execute(run_daemon)
    execute(run_certainty_queue)
    execute(run_server)
