from sqlalchemy import create_engine
from sqlalchemy.sql.expression import ClauseElement, desc
from sqlalchemy.orm import relationship, backref
from sqlalchemy import (Column, Integer, String, Table,
                        DateTime, Boolean, Float, ForeignKey)
engine = create_engine('sqlite:///database.db', echo=False)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

association_table = Table('association', Base.metadata,
    Column('job_id', Integer, ForeignKey('jobs.id')),
    Column('node_id', Integer, ForeignKey('nodes.id')))

__all__ = ['Job', 'Node', 'Cluster', 'Snapshot', 'Queue',
           'get_or_create', 'create_all', 'add_jobs_from_dict',
           'add_nodes_from_dict', 'engine']

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


class Cluster(Base):
    __tablename__ = 'clusters'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)


class Snapshot(Base):
    __tablename__ = 'snapshots'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime())    


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


def add_jobs_from_dict(db, jobsdict, snapshot, cluster):
    for d in jobsdict.itervalues():
        keys = ['status', 'priority', 'processors', 'nodes',
                'user', 'error', 'name', 'job_id', 'n_nodes']
        sanitized = dict(((k, v) for k, v in d.iteritems() if k in keys))
        job = Job(**sanitized)
        job.cluster = cluster
        job.snapshot = snapshot
        
         # add the queue that this job is on
        q, _ = get_or_create(db, Queue, name=d['queue'], cluster=cluster)
                             
        job.queue = q
        db.add(job)


def add_nodes_from_dict(db, nodesdict, snapshot, cluster):
    for d in nodesdict:
        keys = ['name', 'state', 'load', 'n_procs', 'n_running']
        sanitized = dict(((k, v) for k, v in d.iteritems() if k in keys))
        node = Node(**sanitized)
        node.cluster = cluster
        node.snapshot = snapshot
        
        # connect the node to the jobs
        for job_id in d['job_ids']:
            node.jobs.append(db.query(Job).filter_by(job_id=job_id, cluster=cluster,
                                                     snapshot=snapshot).first())
         
        # register what queues this node acts on
        for queue_name in d['queues']:
            q, _ = get_or_create(db, Queue, name=queue_name, cluster=cluster)
            node.queues.append(q)
         
        db.add(node)


def _testbuild():    
    import datetime
    import json

    with open('dump.json') as f:
        report = json.load(f)
        snapshot = Snapshot(time=datetime.datetime.now())
        cluster = Cluster(name='test')

        add_jobs_from_dict(db, report['jobs'], snapshot, cluster)
        add_nodes_from_dict(db, report['nodes'], snapshot, cluster)
    db.commit()




if __name__ == '__main__':
    import analytics
    from sqlalchemy.orm import scoped_session, sessionmaker
    db = scoped_session(sessionmaker(bind=engine))

    create_all()
    #_testbuild()

    print analytics.procs_by_user(db, db.query(Cluster).filter_by(name='test').first())
