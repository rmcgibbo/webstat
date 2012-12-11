# python
from datetime import datetime
import time

# sql
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import ClauseElement, desc
from sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker
from sqlalchemy import (Column, Integer, String, Table,
                        DateTime, Boolean, Float, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base

# this project
import settings

engine = create_engine('sqlite:///database.sqlite3', echo=False)
Base = declarative_base()
db = scoped_session(sessionmaker(bind=engine))

association_table = Table('association', Base.metadata,
    Column('job_id', Integer, ForeignKey('jobs.id')),
    Column('node_id', Integer, ForeignKey('nodes.id')))

__all__ = ['Job', 'Node', 'Cluster', 'Snapshot', 'Queue',
           'get_or_create', 'create_all', 'add_jobs_from_dict',
           'add_nodes_from_dict', 'engine', 'db']

class Job(Base):
    __tablename__ = 'jobs'
    id =  Column(Integer, primary_key=True)
    job_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    user = Column(String(200), nullable=False)
    processors =  Column(Integer)
    priority = Column(Integer)
    status = Column(String(200), nullable=False)
    n_nodes =  Column(Integer, nullable=False)
    error = Column(String(200), nullable=True)

    # three many-> one
    queue_id = Column(Integer, ForeignKey('queues.id'))
    queue = relationship("Queue", backref='jobs', order_by=id)
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    cluster = relationship("Cluster", backref='jobs', order_by=id)
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))
    snapshot = relationship("Snapshot", backref='jobs', order_by=id)

    def __repr__(self):
        return '< Job: %s name=%s user=%s, queue=%s, snapshot=%s>' % (self.job_id,
            self.name, self.user, self.queue.name, self.snapshot_id)

    def to_dict(self):
        raise NotImplementedError

class Node(Base):
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    state = Column(String(200), nullable=False)
    load = Column(Float)
    n_procs = Column(Integer)
    n_running = Column(Integer)

    # many nodes -> one job
    jobs = relationship("Job", secondary=association_table,
                        backref="nodes")
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    cluster = relationship("Cluster", backref='nodes', order_by=id)
    # many nodes -> one snapshot
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))
    snapshot = relationship("Snapshot", backref='nodes', order_by=id)


    def __repr__(self):
        return '< Node:%s -- state=%s, n_procs=%s, n_running=%s, snapshot=%s >' % \
            (self.name, self.state, self.n_procs, self.n_running,
            self.snapshot_id)

    def to_dict(self):
        return {'cluster': self.cluster.name,
                'load': self.load,
                'n_procs': self.n_procs,
                'n_running': self.n_running,
                'name': self.name,
                'state': self.state}


class Queue(Base):
    __tablename__ = 'queues'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)

    # many queues -> one node
    node_id = Column(Integer, ForeignKey('nodes.id'))
    node = relationship('Node', backref='queues', order_by=id)
    # many queues -> one cluster
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    cluster = relationship("Cluster", backref='queues', order_by=id)

    def __repr__(self):
        return '< Queue: %s >' % (self.name, )


class Cluster(Base):
    __tablename__ = 'clusters'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)

    def __repr__(self):
        return '< Cluster name=%s >' % (self.name,)


class Snapshot(Base):
    __tablename__ = 'snapshots'
    id = Column(Integer, primary_key=True)
    
    # unix timestamp
    timestamp = Column(Float)
    
    def __init__(self):
        self.timestamp = time.time()
        
    @property
    def time(self):
        return datetime.fromtimestamp(self.timestamp, settings.timezone)
        

    def __repr__(self):
        return '< Snapshot: time=%s >' % (self.time.strftime('%c'),)


def create_all():
    Base.metadata.create_all(engine)


def get_or_create(session, model, **kwargs):
    #http://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
    instance = session.query(model).filter_by(**kwargs).first()

    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        instance = model(**params)
        session.add(instance)
        return instance, True


def add_jobs_from_dict(db, jobslist, snapshot, cluster):
    "add data sent by the daemons to the database"
    
    for j in jobslist:
        keys = ['status', 'priority', 'processors', 'nodes',
                'user', 'error', 'name', 'job_id', 'n_nodes']
        sanitized = dict(((k, v) for k, v in j.iteritems() if k in keys))
        job = Job(**sanitized)
        job.cluster = cluster
        job.snapshot = snapshot

         # add the queue that this job is on
        q, _ = get_or_create(db, Queue, name=j['queue'], cluster=cluster)

        job.queue = q
        db.add(job)


def add_nodes_from_dict(db, nodeslist, snapshot, cluster):
    "add data sent by the daemons to the database"

    n_nodes = db.query(Node).count()
    for n in nodeslist:
        keys = ['name', 'state', 'load', 'n_procs', 'n_running']
        sanitized = dict(((k, v) for k, v in n.iteritems() if k in keys))
        node = Node(**sanitized)
        node.cluster = cluster
        node.snapshot = snapshot

        # connect the node to the jobs
        for job_id in n['job_ids']:
            node.jobs.append(db.query(Job).filter_by(job_id=job_id, cluster=cluster,
                                                     snapshot=snapshot).first())

        # register what queues this node acts on
        for queue_name in n['queues']:
            q, _ = get_or_create(db, Queue, name=queue_name, cluster=cluster)
            node.queues.append(q)

        db.add(node)
    db.flush()
    print 'added %s nodes' % (db.query(Node).count() - n_nodes)


def _testbuild():
    "testing code"
    import datetime
    import json

    with open('etc/dump.json') as f:
        report = json.load(f)
        snapshot = Snapshot(time=datetime.datetime.now())
        cluster = Cluster(name='test')

        add_jobs_from_dict(db, report['jobs'], snapshot, cluster)
        add_nodes_from_dict(db, report['nodes'], snapshot, cluster)
    db.commit()




if __name__ == '__main__':
    "testing code"
    import analytics

    create_all()
    #_testbuild()

    print analytics.procs_by_user(db, db.query(Cluster).filter_by(name='test').first())
