dispatch = function(event) {
    console.log("Received data on the socket!");
    $('body').append('<div>' + event.data + '</div>');
}

main = function() {
    console.log("Starting the function");
    var ws = new WebSocket("ws://vspm42-ubuntu.stanford.edu:/socket");
    console.log("Socket opened");
    ws.onmessage = dispatch;
    $('body').append('<div id="> Start! </div>');
  
};