$ = jQuery
window.main = () ->
    dispatch = (event) ->
        # dispatch a websocket event to the appropriate handler
        msg = JSON.parse(event.data)

        if msg.name == 'procs_by_user'
            proc_by_user(msg.contents)
        else
            console.log('No matching handler for message.')
            console.log(msg)
            alert('error')
    
    # handle drawing a pie graph
    proc_by_user = (payload) ->
        # websocket handler for proc_by_user graph
        
        # change turn the data into a 2D array
        table = [['User', 'Procs']]
        table.push [user, procs] for user, procs of payload.data
        # put it into google's format
        data = google.visualization.arrayToDataTable(table)

        options =
            title: "Procs By User: #{payload.cluster}"

        chart = new google.visualization.PieChart($('#chart_div')[0])
        chart.draw(data, options)
        
        console.log('updated!')
    
    # start up the websocket
    console.log("Stating the socket")
    ws = new WebSocket("ws://vspm42-ubuntu.stanford.edu:/socket")
    ws.onmessage = dispatch
    
    $('a#refresh').click ->
        $.get('/refresh')
           
            




             