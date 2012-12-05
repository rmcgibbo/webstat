# qstat
*web monitoring for distributed set of PBS queues*

### concept

Simple web page aranged as a rectangular grid. Each row represents a cluster/PBS system. Within the rows, you have
a few pie and line charts showing the current usage of the cluster. The graphs might be a pie chart of the current
usage of the queue by user / group, a line-chart of the past history of usage by user, etc.

![Sketch](http://awwapp.com/s/b0/ea/be.png)

### architecture
0. Three moving parts. Two connection protocols
    - Python daemons running on each cluster
    - Tornado webserver. Polls the daemons for data and pushes a summary to the browsers.
    - Browser javascript. Receieves push data from the server, renders it as charts
    - Daemon-server communication is pyzmq over ssh
    - browser-server communication is websockets
1. Lee-Ping already has a python code for calling qstat and checkjob to take a snapshot of the data usage.
https://github.com/rmcgibbo/hpcutils/blob/master/scripts/PBSCheck.py. The script is current designed to output to the
shell, but with a little modification it could probably output its info in a structured JSON/XML format. This script
will be running on the clusters in a daemon mode.
2. The web server, at some time interval, will connect to all of the daemons and ask them for a report. They will send
back the JSON indicating the current usage. If the webserver does not get a response, it not crash and will be able to
show the user that "monitoring is down, check the daemon status" or whatever.
3. The connection will by using pyzeromq tunneled over ssh. http://zeromq.github.com/pyzmq/ssh.html
4. The web server will save the data in a sqlite3 (or whatever) database.
5. All of the display logic will be in the browser.
6.  Server will continuously send the most recent data to the client, pulled from its sqlite database. It will
send only when it gets new data (or when a new browser connects). Browser will display data to user with an external javascript
plotting package, like google charts https://google-developers.appspot.com/chart/interactive/docs/quick_start.
This looks pretty easy.
7. Connection between the browser and the server will be via websocket
8. What technology should run the server? Perhaps tornado, as it looks like it runs easily with websockets. http://blog.kagesenshi.org/2011/10/simple-websocket-push-server-using.html
Django does not appear to be a great fit for the async aspect.
9. The server does not need to do much -- just aggregate data from the daemons and then send it to the browsers on request.
10. Database should be sqlite3 via sqlalchemy. This is fine because the browser is never updating the db, so theads aren't
an issue. The db is only updated via the server side timer that polls the daemons.
