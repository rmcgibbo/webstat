$ = jQuery

# data = 
#     vsp-compute: null
#     certainty: null

render_mustache = (template_id, destination_id, data) ->
    tpl = $(template_id).html()
    html = Mustache.to_html(tpl, data)
    $(destination_id).html(html)


procs_per_user = (payload) ->
    table = new google.visualization.DataTable()
    table.addColumn('string', 'User')
    table.addColumn('number', 'Procs')
    for row in payload.data
        # payload is 'Procs', 'User', so we need to reverse it
        table.addRow([row[1], row[0]])
    
    options =
        chartArea: {'width': '100%', 'height': '80%'},
    #    title: "Procs By User - #{payload.cluster}"
        
    plot = 
        table: table
        options: options
        time: payload.time


nodes_by_status = (payload) -> 
    table = new google.visualization.DataTable()
    table.addColumn('string', 'Status')
    table.addColumn('number', 'Number')
    for row in payload.data
        # payload is 'Procs', 'User', so we need to reverse it
        table.addRow([row[1], row[0]])

    options =
        chartArea: {'width': '100%', 'height': '80%'},
        #title: "Nodes - #{payload.cluster}"

    plot = 
        table: table
        options: options
        time: payload.time

draw = (plot, destination) ->
     chart = new google.visualization.PieChart(destination[0])
     chart.draw(plot.table, plot.options)  

main = ->
    data = 
        clusters: [{name: 'vsp-compute', active: true},
                   {name: 'other', active: false}]
               
    render_mustache("#tpl_navbar", "#navbar", data);
    render_mustache("#tpl_content", "#content", data);
    
    $.get '/procs', (e) ->
        data.clusters[0].procs_plot = procs_per_user(e)
    $.get '/nodes', (e) ->
        data.clusters[0].nodes_plot = nodes_by_status(e)

    $("#nav-vsp-compute").click (e) ->
      e.preventDefault()
      $(this).tab('show')
      draw(data.clusters[0].procs_plot, $('#vsp-compute .chart1'))
      draw(data.clusters[0].nodes_plot, $('#vsp-compute .chart2'))


console.log("MMmm coffee!") 
#first load up the charts API, then call the main method
google.load("visualization", "1", {packages:["corechart"]});
google.setOnLoadCallback(main);
