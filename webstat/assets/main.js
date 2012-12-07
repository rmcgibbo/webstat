(function() {
  var $;

  $ = jQuery;

  window.proc_by_user = function(event) {
    var chart, data, options;
    console.log('proc by user');
    data = google.visualization.arrayToDataTable([['Task', 'Hours per Day'], ['Work', 11], ['Eat', 2], ['Commute', 2], ['Watch TV', 2], ['Sleep', 7]]);
    options = {
      title: 'My Daily Activities'
    };
    chart = new google.visualization.PieChart($('#chart_div')[0]);
    chart.draw(data, options);
    return $('body').append('<div>' + event.data + '</div>');
  };

  window.main = function() {
    var ws;
    console.log("Stating the socket");
    ws = new WebSocket("ws://vspm42-ubuntu.stanford.edu:/socket");
    ws.onmessage = window.dispatch;
    return $('body').append('<div id="> Start! </div>');
  };

  window.dispatch = function(event) {
    var msg;
    msg = JSON.parse(event.data);
    console.log(msg.name);
    if (msg.name === 'proc_by_user') return console.log('!');
  };

}).call(this);
