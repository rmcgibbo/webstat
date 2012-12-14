#!/usr/env python

import os, sys, socket
import json
import zmq
import daemon
import lockfile

class Job:
    def __init__(self):
        self.job_id = 0
        self.name = None
        self.user = None
        self.processors = 0
        self.priority = 0
        self.queue = None
        self.status = None
        self.n_nodes = 1
        self.error = None

    def as_dict(self):
        return self.__dict__


class Node:
    def __init__(self):
        self.name = None
        self.state = None
        self.load = 0.0
        self.n_procs = 0
        self.n_running = 0
        self.job_ids = []
        self.queues = []

    def as_dict(self):
        return self.__dict__


class Cluster:
    @property
    def jobs(self):
        "All the jobs running on the cluster (list of Jobs)"
        return self._jobs

    @property
    def nodes(self):
        "All of the nodes on the cluster (list of Nodes)"
        return self._nodes

    @property
    def groups(self):
        "User -> group mapping (dict)"
        return self._groups


    def __init__(self):
        # Names of commands sent to the queueing system
        self.qstat_command = 'qstat -f -1'
        self.nodes_command = 'pbsnodes'
        self.diagnose_priorities = 'diagnose -p'
        self.diagnose_errors = 'diagnose -q'
        self.checknode_command = 'checknode '

        self._jobs = []
        self._nodes = []
        self._groups = {}

        # get everything started
        self.init_jobs()        # Creates self.jobs
        self.init_nodes()       # Makes the list of nodes
        self.init_groups()      # gets user -> group mapping

    def init_jobs(self):
        # Build a list of jobs.

        # first we're going to put the jobs in a dict
        # by job_id, to avoid redundancies, and then
        # we'll transfer it to a list at the end
        jobs_dict = {}
        cjob = None

        for line in os.popen(self.qstat_command):
            if len(line.split()) == 0:
                continue
            elif line[:7] == "Job Id:":
                if cjob != None:
                    jobs_dict[cjob.job_id] = cjob
                # Initialize the new class
                cjob = Job()
                cjob.job_id = int(line.split()[-1].split('.')[0].split('[')[0])
            elif line.split()[0] == "Job_Owner":
                cjob.user = line.split()[-1].split('@')[0]
            elif line.split()[0] == "Job_Name":
                cjob.name = line.split()[-1]
            elif line.split()[0] == "queue":
                cjob.queue = line.split()[-1]
            elif line.split()[0] == "exec_host":
                exec_hosts = [i.split('/')[0] for i in line.split()[-1].split('+')]
                if "certainty" in socket.gethostname():
                    cjob.processors = len(set(exec_hosts)) * 24
                else:
                    cjob.processors = len(exec_hosts)
            elif line.split()[0] == "Resource_List.nodect":
                # The "job-exclusive" and "free" states are not informative
                cjob.n_nodes = int(line.split()[-1])
            elif line.split()[0] == "job_state":
                # Job is queued
                if line.split()[-1] == "Q":
                    cjob.status = "Q"
                # Job is running
                elif line.split()[-1] == "R":
                    cjob.status = "R"
                # Job is on hold
                elif line.split()[-1] == "H":
                    cjob.status = "H"
                # Job is in error state
                elif line.split()[-1] == "E":
                    cjob.status = "E"
                else:
                    print "I don't know what to do with this:"
                    print line,
        jobs_dict[cjob.job_id] = cjob

        # run the initialization delegates
        self._init_job_errors(jobs_dict)
        self._init_job_priorities(jobs_dict)

        # put the jobs into a list
        self.jobs = jobs_dict.values()

    def _init_job_errors(self, jobs_dict):
        # errors for queued jobs that don't have priorities
        for line in os.popen(self.diagnose_errors):
            if len(line.split()) < 3:
                continue
            try:
                jobs_dict[int(line.split()[1])].error = ' '.join(line.split()[2:])
            # Sometimes the first word is not an integer, ignore this error.
            except ValueError:
                continue

    def _init_job_priorities(self, jobs_dict):
        # List of priority values for queued jobs
        for line in os.popen(self.diagnose_priorities):
            if len(line.split()) < 2:
                continue
            try:
                jobs_dict[int(line.split()[0])].priority = int(line.split()[1])
            # Sometimes the first word is not an integer, ignore this error.
            except ValueError:
                continue


    def init_nodes(self):
        # Build a list of nodes.
        cnode = None
        for line in os.popen(self.nodes_command):
            if len(line.split()) == 0:
                continue
            # I recognize that the line corresponds to a node name if
            elif len(line.split()) == 1 and line[0] != " ":
                if cnode != None:
                    self.nodes.append(cnode)
                # Initialize the new class
                cnode = Node()
                cnode.queues = []
                cnode.name = line.strip()
                cnode.job_ids = []
            elif line.split()[0] == "np":
                cnode.n_procs = int(line.split()[-1])
            elif line.split()[0] == "jobs":
                cnode.job_ids = list(set([int(i.split("/")[-1].split('.')[0].split('[')[0]) for i in line.split("=")[-1].split(",")]))
                cnode.n_running = len(line.split()) - 2
            elif line.split()[0] == "status":
                # The mighty genexp
                # Splits the line by commas, and for each chunk, check if the field before equals sign is "loadave".
                # If so, set Load equal to the field after equals sign.
                cnode.load = float((i.split('=')[1] for i in line.split(',') if i.split('=')[0] == 'loadave').next())
            elif line.split()[0] == "state":
                #print cnode.state
                # The "job-exclusive" and "free" states are not informative
                cnode.state = line.split()[-1]
                #cnode.state = line.split()[-1].replace('free','').replace('job-exclusive','')
            elif line.split()[0] == "properties":
                # The "job-exclusive" and "free" states are not informative
                cnode.queues = line.split()[-1].split(",")

        self.nodes.append(cnode)


    def init_groups(self):
        self.groups = {}
        for job in self.jobs:
            try: # Sometimes the group file isn't readable
                group = os.popen('grep %s /etc/group' % user).readlines()[0].split(':')[0]
            except:
                group = None
            if job.user is not None:
                self.groups[job.user] = group


def make_report():
    c = Cluster()
    report = {'jobs': [e.as_dict() for e in c.jobs],
              'nodes': [e.as_dict() for e in c.nodes],
              'groups': c.groups}
    return report


def main():
    ctx = zmq.Context()
    sock = ctx.socket(zmq.REP)
    sock.bind('tcp://*:7621')
    auth_key = None

    while 1:
        recvd = sock.recv()
        print 'recvd', recvd
        #if auth_key is None:
        #    auth_key = recvd
        #else:
        #    if auth_key != recvd:
        #        sock.send('')
        report = make_report()
        print 'Send Report, n_nodes=%s, n_jobs=%s' % (len(report['nodes']), len(report['jobs']))
        sock.send_json(report)


if __name__ == "__main__":
    print 'Usage %s [shell, run, daemon]' % sys.argv[0]
    if len(sys.argv) == 1:
        sys.exit(1)

    if sys.argv[1] == 'shell':
        print 'report = make_report()'
        report = make_report()
        import IPython; IPython.embed()

    elif sys.argv[1] == 'run':
        main()

    elif sys.argv[1] == 'daemon':
        with daemon.DaemonContext(pidfule=lockfile.FileLock('/var/run/webstatd.py')):
            main()

    else:
        raise RuntimeError()
