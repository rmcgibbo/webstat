(function() {
  var $, draw, main, nodes_by_status, procs_per_user, render_mustache;

  $ = jQuery;

  render_mustache = function(template_id, destination_id, data) {
    var html, tpl;
    tpl = $(template_id).html();
    html = Mustache.to_html(tpl, data);
    return $(destination_id).html(html);
  };

  procs_per_user = function(payload) {
    var options, plot, row, table, _i, _len, _ref;
    table = new google.visualization.DataTable();
    table.addColumn('string', 'User');
    table.addColumn('number', 'Procs');
    _ref = payload.data;
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      row = _ref[_i];
      table.addRow([row[1], row[0]]);
    }
    options = {
      chartArea: {
        'width': '100%',
        'height': '80%'
      }
    };
    return plot = {
      table: table,
      options: options,
      time: payload.time
    };
  };

  nodes_by_status = function(payload) {
    var options, plot, row, table, _i, _len, _ref;
    table = new google.visualization.DataTable();
    table.addColumn('string', 'Status');
    table.addColumn('number', 'Number');
    _ref = payload.data;
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      row = _ref[_i];
      table.addRow([row[1], row[0]]);
    }
    options = {
      chartArea: {
        'width': '100%',
        'height': '80%'
      }
    };
    return plot = {
      table: table,
      options: options,
      time: payload.time
    };
  };

  draw = function(plot, destination) {
    var chart;
    chart = new google.visualization.PieChart(destination[0]);
    return chart.draw(plot.table, plot.options);
  };

  main = function() {
    var data;
    data = {
      clusters: [
        {
          name: 'vsp-compute',
          active: true
        }, {
          name: 'other',
          active: false
        }
      ]
    };
    render_mustache("#tpl_navbar", "#navbar", data);
    render_mustache("#tpl_content", "#content", data);
    $.get('/procs', function(e) {
      data.clusters[0].procs_plot = procs_per_user(e);
      return draw(data.clusters[0].procs_plot, $('#vsp-compute .chart1'));
    });
    return $.get('/nodes', function(e) {
      data.clusters[0].nodes_plot = nodes_by_status(e);
      return draw(data.clusters[0].nodes_plot, $('#vsp-compute .chart2'));
    });
  };

  $("#nav-vsp-compute").click(function(e) {
    e.preventDefault();
    console.log('myclick!');
    return $(this).tab('show');
  });

  console.log("MMmm coffee!");

  google.load("visualization", "1", {
    packages: ["corechart"]
  });

  google.setOnLoadCallback(main);

}).call(this);
