from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, backref
from sqlalchemy import (Column, Integer, String, Table,
                        DateTime, Boolean, Float, ForeignKey)
engine = create_engine('sqlite:///database.db', echo=False)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

association_table = Table('association', Base.metadata,
    Column('job_id', Integer, ForeignKey('jobs.id')),
    Column('node_id', Integer, ForeignKey('nodes.id'))
)

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
    
    #many jobs -> one queue
    queue_id = Column(Integer, ForeignKey('queues.id'))
    queue = relationship("Queue", backref='jobs')


    time = Column(DateTime())

class Node(Base):
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True)
    state = Column(String(200), nullable=False)
    load = Column(Float)
    n_procs = Column(Integer)
    n_running = Column(Integer)

    # many nodes -> one job
    jobs = relationship("Job", secondary=association_table, 
                        backref="nodes")

    time = Column(DateTime())


class Queue(Base):
    __tablename__ = 'queues'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)

    # many queues -> one node
    node_id = Column(Integer, ForeignKey('nodes.id'))
    node = relationship('Node', backref='queues', order_by=id)

def create_all():
    Base.metadata.create_all(engine)
