# [webstat](http://vspm42-ubuntu.stanford.edu)
*web monitoring interface for a distributed set of PBS queues*

![Prototype](https://raw.github.com/rmcgibbo/webstat/master/webstat.png)
As you see, there are no free nodes because Lee-Ping is using them all.

### concept

Wouldn't it be nice to have a live-updating browser-based graphical summary of
the current state of the queue and usage of all of our clusters?
Yeah. I think so too.

### architecture
There are three components to the system: (a) browser app, (b) webserver, and
(c) cluster daemons.

The cluster daemons are the simplest. They are small daemonized python processes
running on each cluster. Their only functionality is to query the state of the
cluster via PBS shell commands like `qstat`, parse the output into a nice format,
and send it to the webserver. The code is based on Lee-Ping's [PBSCheck.py](https://github.com/rmcgibbo/hpcutils/blob/master/scripts/PBSCheck.py)
Communication is done over a zeromq REQ/REP socket. The cluster deamon is the REP (reply) end.

The webserver is a python process running the [tornado](http://www.tornadoweb.org/)
server. I chose tornado because it's fairly simple and has some support for
websockets that are lacking from something like django. The webserver is using
sqlite3 with sqlalchemy to hold its data and memcached
([pylibmc](http://pypi.python.org/pypi/pylibmc)) for fun. At some periodic interval,
the webserver requests new data from the daemons. It also allows the clients
to trigger this refresh manually.

To the client, the server simply responds to AJAX requests for data. So I'm
not using any server-side templating. Well, it also does one other thing, which
is manage a websocket connection with the browsers. Whenever the server receives
new data from the daemons, it pushes out an announcement to that effect over the
websocket to each connected client, which basically invites the clients to
ask for the data. The server is deployed behind HAProxy on vspm42-ubuntu.

The client itself is a javascript app. It's hosted, currently, in a [separate
github repository](https://github.com/rmcgibbo/webstatclient). That code is
written in coffeescript, uses the Spine.js framework, twitter bootsrap
for UI components and google charts for graphing. It's the trickiest part of
the whole operation because it requires using a new language an ecosystem.

todo
----
- more visualizations, data
- more clusters (biox3)
- move some logic that's in the client into this codebase. specifically, 
  the client is currently doing some data munging to get the data from
  the format the sqlite3 spits out into a format that google charts likes.
  it would be easier if this logic were on the python side (and it just emmitted
  the data in a format that google charts likes)
- Make the server run as a daemon and handle logging correctly. Probably using
  [this module](http://pypi.python.org/pypi/python-daemon/)  
- Make the whole thing installable as a python package and easy to run from
  the command line, so that it can be deployed easily with
  [fabric](http://docs.fabfile.org/en/1.5/).
- put the client and server code together in a single package.
- it would be really nice to be able to see the state of the queue -- which jobs are queued,
  what priority they have, etc. Be able to live-filter that to only show a specific username or
  job name. Be able to get details about the job. This requires thinking a little harder
  about the routes and the API the server is providing.
