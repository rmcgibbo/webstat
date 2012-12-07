#!/usr/env python

import os, sys, socket
import json
import zmq
from daemonize import Daemonize

# This is meant to be a standalone script.

class Cluster:
    #  Attributes of the cluster that we're interested in
    jobs = {}            # All the jobs running on the cluster
    nodes = []           # All of the nodes on the cluster
    user_slots = {}      # Number of slots taken by user
    groups     = {}      # Names of research groups (useful only on large clusters)

    def __init__(self):
        # Names of commands sent to the queueing system
        self.qstat_command = 'qstat -f -1'
        self.nodes_command = 'pbsnodes'
        self.diagnose_priorities = 'diagnose -p'
        self.diagnose_errors = 'diagnose -q'
        self.checknode_command = 'checknode '

        # get everything started
        self.init_jobs()        # Creates self.jobs
        self.init_nodes()       # Makes the list of nodes
        self.init_user_slots()  # Summarizes number of slots taken by user
        
    def init_jobs(self):
        # Build a list of jobs.
        cjob = None
        for line in os.popen(self.qstat_command):
            if len(line.split()) == 0:
                continue
            elif line[:7] == "Job Id:":
                if cjob != None:
                    self.jobs[cjob.job_id] = cjob
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
        self.jobs[cjob.job_id] = cjob

        # run the initialization delegates
        self._init_job_errors()
        self._init_job_priorities()


    def _init_job_errors(self):
        # errors for queued jobs that don't have priorities
        for line in os.popen(self.diagnose_errors):
            if len(line.split()) < 3:
                continue
            try:
                self.jobs[int(line.split()[1])].error = ' '.join(line.split()[2:])
            # Sometimes the first word is not an integer, ignore this error.
            except ValueError:
                continue

    def _init_job_priorities(self):
        # List of priority values for queued jobs
        for line in os.popen(self.diagnose_priorities):
            if len(line.split()) < 2:
                continue
            try:
                self.jobs[int(line.split()[0])].priority = int(line.split()[1])
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


    def init_user_slots(self):
        # From the jobs-dictionary, figure out which users are using how many slots
        self.user_slots = {}
        self.groups = {}
        for job_number in self.jobs:
            job = self.jobs[job_number]
            user = job.user
            try: # Sometimes the group file isn't readable
                group = os.popen('grep %s /etc/group' % user).readlines()[0].split(':')[0]
            except:
                group = "NoGroup"
            np   = job.processors
            self.groups[user] = group
            if user not in self.user_slots:
                self.user_slots[user] = np
            else:
                self.user_slots[user] += np


class Job:
    def __init__(self):
        self.job_id = 0
        self.name = 'NoName'
        self.user = 'Nobody'
        self.processors = 0
        self.priority = 0
        self.queue = 'NoQueue'
        self.status = 'NoStatus'
        self.n_nodes = 1
        self.error = None

    def _as_json_encodable(self):
        return self.__dict__
    
class Node:
    def __init__(self):
        self.name = 'NoName'
        self.state = 'NoState'
        self.load = 0.0
        self.n_procs = 0
        self.n_running = 0
        self.job_ids = []
        self.queues = []

    def _as_json_encodable(self):
        return self.__dict__


class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            # if the object has a json encodable representation
            # registered, use that
            return obj._as_json_encodable()
        except:
            # else just try the object
            return obj

            
def report():
    c = Cluster()
    report = {'jobs': c.jobs, 'nodes': c.nodes,
              'user_slots': c.user_slots,
              'groups': c.groups}
    return json.dumps(report, cls=MyJSONEncoder)

def main():
    ctx = zmq.Context()
    sock = ctx.socket(zmq.REP)
    sock.bind('tcp://*:76215')
    auth_key = None
    
    while 1:
        recvd = sock.recv()
        print 'recvd', recvd
        if auth_key is None:
            auth_key = recvd
        else:
            if auth_key != recvd:
                sock.send('')
        print 'Send Report'
        sock.send(report())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'shell':
            print report()
        else:
            main()
    else:
        daemon = Daemonize(app='cluster_daemon', pid = "/tmp/cluster_daemon.pid", action=main)
        print 'Daemonizing' 
        daemon.start()
