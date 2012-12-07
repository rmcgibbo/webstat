from sqlalchemy.sql.expression import desc
from collections import defaultdict
from models import *

def most_recent_poll(db, model, cluster):
    snapshots = db.query(Snapshot).order_by(desc(Snapshot.time))
    for i in xrange(snapshots.count()):
        q = db.query(model).filter_by(cluster=cluster, snapshot=snapshots.get(i))
        if q.count() != 0:
            return q.all()

def procs_by_user(db, cluster):
    p_by_user = defaultdict(lambda: 0)

    for job in most_recent_poll(db, Job, cluster):
        p_by_user[job.user] += job.processors

    return dict(p_by_user)
