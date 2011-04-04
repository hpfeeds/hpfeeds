var loaddiv = $('<div/>', { class: 'center' }).append($("<img/>", { src: '/static/load.gif'}));

function Channels(container) {
	this.container = container;

	this.render = function()
	{
		var list = $("<ul/>");

		for(i in this.data)
		{
			var item = this.data[i];
			var link = $("<a/>", { href: '#' });
			link.text(item[0]);
			link.bind('click', function(obj, chan) { return function () {
				console.log(obj, chan);
			} }(this, item));
			list.append($("<li/>").append(link));
		}

		this.container.empty().append(list);
	};

	this.container.append(loaddiv);

	$.post('/aj/channels', function(obj) { return function (result) {
		obj.data = result;
		obj.render();
	} }(this), 'json' );
}

function Authkeys(container) {
	this.container = container;

	this.render = function()
	{
		var list = $("<ul/>");

		for(i in this.data)
		{
			var item = this.data[i];
			var link = $("<a/>", { href: '#' });
			link.text(item);
			link.bind('click', function(obj, item) { return function () {
				console.log(obj, item);
			} }(this, item));
			list.append($("<li/>").append(link));
		}

		this.container.empty().append(list);
	};

	this.container.append(loaddiv);

	$.post('/aj/authkeys', function(obj) { return function (result) {
		obj.data = result;
		obj.render();
	} }(this), 'json' );
}

$(document).ready(function() {
	window.channels = new Channels($("#channels"));
	window.authkeys = new Authkeys($("#authkeys"));
})

