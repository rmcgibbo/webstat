from sqlalchemy.sql.expression import desc
from sqlalchemy import func
from collections import defaultdict
from datetime import timedelta, datetime
import time

import settings
from models import *
from memcached import memcached


def most_recent_snapshot(model, cluster):
    snapshots = db.query(Snapshot).order_by(desc(Snapshot.timestamp))
    for snapshot in snapshots.all():
        q = db.query(model).filter_by(cluster=cluster, snapshot=snapshot)
        if q.count() > 0:
            return snapshot


def recent_snapshots(model, cluster, time_delta):
    now = datetime.now(tz=settings.timezone)

    # as a unix timestamp
    before = time.mktime((now - time_delta).timetuple())
    
    all_snapshots = db.query(Snapshot).order_by(desc(Snapshot.timestamp)).\
        filter(Snapshot.timestamp > before)
        
    snapshots = []
    
    for s in all_snapshots.all():
        q = db.query(model).filter_by(cluster=cluster, snapshot=s)
        if q.count() > 0:
            snapshots.append(s)
    return snapshots


@memcached
def procs_per_user(cluster, time_delta=None):
    """Get the numer of procs in use by each user

    Looks for jobs with status='R', and then also looks for nodes with
    state='free'
    
    Parameters
    ----------
    cluster : Cluster
        What cluster?
    time_delta : str, optional
        If you call this method with a time_delta, you'll get just the most
        recent results. If you ask for a time_delta, it will return a list
        containing the basic return value, but at rach timestep
        
        
    Returns (time_delta=None)
    -------------------------
    data : list of (int, user) tuples
    time : datetime.datetime

    Returns (otherwise)
    -----------------
    timeseries : list of (data, time) tuplies
        A timeseries of the above
    
    Examples
    --------
    >>> procs_per_user(db.query(Cluster).first())
    ([(456, u'leeping'),
      (96, u'sryckbos'),
      (48, u'free')],
     datetime.datetime(2012, 12, 8, 8, 37, 49, 931558))
     
     >>> procs_per_user(db.query(Cluster).first(), time_delta=timedelta(hours=1))
    [([(480, u'leeping'),
       (96, u'sryckbos'),
       (24, u'free')],
      datetime.datetime(2012, 12, 8, 2, 59, 4, 245729, tzinfo=<DstTzInfo
        'US/Pacific' PST-1 day, 16:00:00 STD>)),
     ([(480, u'leeping'),
       (96, u'sryckbos'),
       (24, u'free')],
      datetime.datetime(2012, 12, 8, 2, 58, 54, 344096, tzinfo=<DstTzInfo
        'US/Pacific' PST-1 day, 16:00:00 STD>))]
    """
    
    def at_snapshot(snapshot):
        p_by_user = db.query(func.sum(Job.processors), Job.user).group_by(Job.user).filter_by(cluster=cluster, snapshot=snapshot,
            status='R').all()
        n_free_procs = db.query(func.sum(Node.n_procs)).filter_by(cluster=cluster,
            snapshot=snapshot, state='free').first()[0]
        p_by_user.append((n_free_procs, u'free'))
        return p_by_user, snapshot.time

    snapshot = most_recent_snapshot(Job, cluster)
    
    if time_delta is None:
        snapshot = most_recent_snapshot(Job, cluster)
        return at_snapshot(snapshot)
        
    return [at_snapshot(s) for s in recent_snapshots(Job, cluster, time_delta)]
        
    
@memcached
def nodes_by_status(cluster, time_delta=None):
    """The number of nodes in each job status

    Parameters
    ----------
    cluster : Cluster
        What cluster?
    time_delta : str, optional
        If you call this method with a time_delta, you'll get just the most
        recent results. If you ask for a time_delta, it will return a list
        containing the basic return value, but at rach timestep

    Returns (time_delta=None)
    -------------------------
    data : list of (int, status) tuples
    time : datetime.datetime
    
    Returns (otherwise)
    -----------------
    timeseries : list of (data, time) tuplies
        A timeseries of the above

    Examples
    --------
    >>> nodes_by_status(db.query(Cluster).first())
    ([(5, u'down'), (2, u'free'), (37, u'job-exclusive')],
     datetime.datetime(2012, 12, 8, 8, 37, 49, 931558))
    """

    snapshot = most_recent_snapshot(Node, cluster)
    def at_snapshot(snapshot):
        r = db.query(func.count(Node.state), Node.state).group_by(Node.state).\
            filter_by(snapshot=snapshot, cluster=cluster).all()
        return r, snapshot.time
    
    if time_delta is None:
        snapshot = most_recent_snapshot(Node, cluster)
        return at_snapshot(snapshot)
    
    return [at_snapshot(s) for s in recent_snapshots(Job, cluster, time_delta)]


@memcached
def free_nodes():
    """Nodes that are free on any cluster, currently

    Returns
    -------
    node_dicts : list of dicts
    """
    nodes = []

    for cluster in db.query(Cluster).all():
        snapshot = most_recent_snapshot(Node, cluster)
        nodes.extend(db.query(Node).filter_by(state='free', snapshot=snapshot,
            cluster=cluster).all())

    return [node.to_dict() for node in nodes]


if __name__ == '__main__':
    recent_snapshots(Node, db.query(Cluster).first(), timedelta(minutes=10))
    import IPython
    IPython.embed()
