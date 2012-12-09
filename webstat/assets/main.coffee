$ = jQuery

procs_per_user = (payload) ->
    table = new google.visualization.DataTable()
    table.addColumn('string', 'User')
    table.addColumn('number', 'Procs')
    for row in payload.data
        # payload is 'Procs', 'User', so we need to reverse it
        table.addRow([row[1], row[0]])
    
    options =
        title: "Procs By User - #{payload.cluster}"

    chart = new google.visualization.PieChart($('#chart_div1')[0])
    chart.draw(table, options)        
    #console.log('updated procs_per_user')
    draw_timestamp(payload.time)


nodes_by_status = (payload) -> 
    table = new google.visualization.DataTable()
    table.addColumn('string', 'Status')
    table.addColumn('number', 'Number')
    for row in payload.data
        # payload is 'Procs', 'User', so we need to reverse it
        table.addRow([row[1], row[0]])

    options =
        title: "Nodes - #{payload.cluster}"

    chart = new google.visualization.PieChart($('#chart_div2')[0])
    chart.draw(table, options)        
    #console.log('updated nodes_by_status')
    #draw_timestamp(payload.time)


draw_timestamp = (time) ->
    $('time.timeago').replaceWith("<time class='timeago' datetime='#{time}'></time>")
    $("time.timeago").timeago()


refresh_data = () ->
    console.log("drawing")
    $.get '/procs', procs_per_user
    $.get '/nodes', nodes_by_status

# export this method to the window context, so it can be called outside
window.main = () ->
    # get the data to render the first graphs
    refresh_data()
    
    # socket for recieving announcements from the server
    # the announcements say "hey, new data is available -- you might want it"
    ws = new WebSocket("ws://vspm42-ubuntu.stanford.edu:/announce")
    ws.onmessage = (event) ->
        # we always send JSON over the wire
        data = JSON.parse(event.data)
        console.log(data)
        if data.name == 'annoucement' and data.payload == "refresh"
            refresh_data()        
    # set the heartbeat
    heartbeat_it = setInterval((->
        ws.send(JSON.stringify(name : 'ping'))
    ), 5000)
    ws.onclose = () ->
        clearInterval(heartbeat_it)
        bootbox.dialog "The ship is sinking!"
            label: 'Danger!'
            class : "danger"
    ws.onerror = (event) ->
        clearInterval(heartbeat_it)
        console.log("ERROR")
        console.log(event.data)
    
    # set the link
    $('a#polldaemons').click ->
        status = ws.send(JSON.stringify(name : 'refresh'))
        console.log("Sent WS request. Status = #{status}")
    


             