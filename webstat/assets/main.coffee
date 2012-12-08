$ = jQuery
window.main = () ->
    procs_per_user = (payload) ->
        table = new google.visualization.DataTable()
        table.addColumn('string', 'User')
        table.addColumn('number', 'Procs')
        for row in payload.data
            # payload is 'Procs', 'User', so we need to reverse it
            table.addRow([row[1], row[0]])
        
        options =
            title: "Procs By User - #{payload.cluster}: #{payload.time}"

        chart = new google.visualization.PieChart($('#chart_div1')[0])
        chart.draw(table, options)        
        console.log('updated!')
        
        # register a click to redraw the chart
        google.visualization.events.addListener chart, 'click', (event) ->
            $.get '/procs', procs_per_user
    
    nodes_by_status = (payload) -> 
        table = new google.visualization.DataTable()
        table.addColumn('string', 'Status')
        table.addColumn('number', 'Number')
        for row in payload.data
            # payload is 'Procs', 'User', so we need to reverse it
            table.addRow([row[1], row[0]])
        
        options =
            title: "Nodes - #{payload.cluster}: #{payload.time}"

        chart = new google.visualization.PieChart($('#chart_div2')[0])
        chart.draw(table, options)        
        console.log('updated!')
        
        # register a click to redraw the chart
        google.visualization.events.addListener chart, 'click', (event) ->
            $.get '/nodes', nodes_by_status

    
    $.get '/procs', procs_per_user
    $.get '/nodes', nodes_by_status
    
    $('a#polldaemons').click ->
        $.get('/polldaemons')
           
            




             