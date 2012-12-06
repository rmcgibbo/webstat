# webstat
*web monitoring interface for a distributed set of PBS queues*

### concept

Wouldn't it be nice to have a live-updating browser-based graphical summary of the current state of the queue and usage
of all of our clusters? Yeah. I think so too.

The web page will be aranged as a simple rectangular grid. Each row represents a cluster/PBS system. Within the rows, you have
a few pie and line charts showing the current usage of the cluster. The graphs might be a pie chart of the current
usage of the queue by user / group, a line-chart of the past history of usage by user, etc.

![Sketch](http://awwapp.com/s/b0/ea/be.png)

### architecture
0. Three moving parts. Two connection protocols
    - Python daemons running on each cluster
    - Tornado webserver. Polls the daemons for data and pushes a summary to the browsers.
    - Browser javascript. Receieves push data from the server, renders it as charts
    - Daemon-server communication is 0MQ (PyZMQ) over ssh. http://zeromq.github.com/pyzmq/ssh.html
    - browser-server communication is websockets
1. Lee-Ping already has a python code for calling qstat and checkjob to take a snapshot of the data usage.
https://github.com/rmcgibbo/hpcutils/blob/master/scripts/PBSCheck.py. The script is current designed to output to the
shell, but with a little modification it could probably output its info as JSON. This script
will be running on the clusters in a daemon mode, responding with this JSON on a zeromq REQ/REP socket.
2. The web server, at some time interval, will connect to all of the daemons and ask them for a report.
4. The web server will save the data in a sqlite3 (or whatever) database.
5. All of the display logic will be in the browser.
6.  Server will send the most recent data to the client, pulled from its sqlite database. Server will push new data
after polling the daemons to the browsers over websocket. Browser will display data to user with an external javascript
plotting package, like google charts https://google-developers.appspot.com/chart/interactive/docs/quick_start.
This looks pretty easy.
7. The server will be running [Tornado](http://www.tornadoweb.org/), written in python. http://blog.kagesenshi.org/2011/10/simple-websocket-push-server-using.html
Django would be nice, but is not a good fit for the async aspect. Websockets are not a good fit for django.
8. The server does not need to do much -- just aggregate data from the daemons and then send it to the browsers on request.
9. The server database will be handled [sqlalchemy](http://www.sqlalchemy.org/) backed by sqlite3.
This is fine because the browser is never updating the db, so theads aren't an issue. The db is only updated
via the server side timer that polls the daemons. All the other async calls from the browsers are read-only.
10. Hosting will be annoying. The options are
    - Use one of our workstations, running behind HAProxy.
    - Amazon EC2 or something in the "cloud". The problem here is that to access the daemons, we're going to need to be inside
the stanford firewall (at least for certainty). I think amazon has a VPN thing (http://aws.amazon.com/vpc/faqs/), but this
is probably complicated and not free.
11. Auth? 
