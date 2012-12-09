(function() {
  var $;

  $ = jQuery;

  window.main = function() {
    var proc_by_user;
    proc_by_user = function(payload) {
      var chart, data, options, procs, table, user, _ref;
      table = [['User', 'Procs']];
      _ref = payload.data;
      for (user in _ref) {
        procs = _ref[user];
        table.push([user, procs]);
      }
      data = google.visualization.arrayToDataTable(table);
      options = {
        title: "Procs By User: " + payload.cluster
      };
      chart = new google.visualization.PieChart($('#chart_div')[0]);
      chart.draw(data, options);
      return console.log('updated!');
    };
    $.get('/refresh', function(data) {
      return console.log(data);
    });
    return $('a#refresh').click(function() {
      return $.get('/refresh');
    });
  };

}).call(this);
