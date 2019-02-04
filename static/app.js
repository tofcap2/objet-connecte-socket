$(function () {
	socket = io.connect('http://' + document.domain + ':' + location.port);
	socket.on('connect', function() {
		$('#status').text('Connecté');
    	socket.emit('client_connected', {data: 'New client!'});
	});

	socket.on('disconnect', function() {
		$('#status').text('Déconnecté');
	});

	socket.on('alert', function (data) {
    	$('#status').text('Connecté');
        $('#RedAlert').attr("hidden", data);
	});

	socket.on('temperature', function (data) {
    	$('#status').text('Connecté');
        $('#tc').html(data[0].toString() + '°');
        $('#tf').html(data[1].toString() + '°');
	});
});