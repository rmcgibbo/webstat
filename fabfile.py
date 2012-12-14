from fabric.api import env, local, cd, run, hosts


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
    code_dir = 'webstat'
    with cd(code_dir):
        run('git pull')
        run('python scripts/cluster_daemon.py daemon')

@roles('server')
def run_server():
    with cd('webstat'):
        run('git pull')
        run('nohup python webstat/app.py')

@roles('certainty-queue')
def run_certainty_queue():
    with cd('webstat'):
        run('git pull')
        run('nohup python scripts/certainty-queue')

def deploy():
    run_daemon()
    run_certainty_queue()
    run_server()
