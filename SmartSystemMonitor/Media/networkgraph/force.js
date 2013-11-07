var w = 800, h = 600, fill = d3.scale.category20();

var vis = d3.select("#chart").append("svg:svg").attr("width", w).attr("height",
		h);

d3.json("/media/networkgraph/force.json", function(json) {
	var force = d3.layout.force().charge(-300).linkDistance(60).nodes(
			json.nodes).links(json.links).size([ w, h ]).start();

	var link = vis.selectAll("link").data(json.links).enter()
			.append("svg:line").attr("class", "link").style("stroke-width",
					function(d) {
						return Math.sqrt(d.value);
					}).attr("x1", function(d) {
				return d.source.x;
			}).attr("y1", function(d) {
				return d.source.y;
			}).attr("x2", function(d) {
				return d.target.x;
			}).attr("y2", function(d) {
				return d.target.y;
			}).call(force.drag);

	var node = vis.selectAll("node").data(json.nodes).enter().append(
			"svg:circle").attr("class", "node").attr("cx", function(d) {
		return d.x;
	}).attr("cy", function(d) {
		return d.y;
	}).attr("r", function(d) {
		return d.size;
	}).style("fill", function(d) {
		return d.color;
	}).call(force.drag);

	var textnode = vis.selectAll("node").data(json.nodes).enter().append(
			"svg:a").attr("xlink:href", function(d) {
		return d.url;
	}).append("svg:text").attr("class", "label").attr("fill", "white").attr(
			"text-anchor", "middle").text((function(d) {
		return d.id;
	})).on("click");

	var textlink = vis.selectAll('link').data(json.links).enter().append(
			'svg:text').attr("class", "textlink").attr("x", function(d) {
		return (d.source.y + d.target.y) / 2;
	}).attr("y", function(d) {
		return (d.source.x + d.target.x) / 2;
	}).attr("text-anchor", "middle").text(function(d) {
		return d.label;
	});

	node.append("svg:title").text(function(d) {
		return d.name;
	});

	force.on("tick", function() {
		link.attr("x1", function(d) {
			return d.source.x;
		}).attr("y1", function(d) {
			return d.source.y;
		}).attr("x2", function(d) {
			return d.target.x;
		}).attr("y2", function(d) {
			return d.target.y;
		});
		node.attr("cx", function(d) {
			return d.x;
		}).attr("cy", function(d) {
			return d.y;
		});
		textnode.attr("transform", function(d) {
			return "translate(" + d.x + "," + d.y + ")";
		});
		textlink.attr("x", function(d) {
			return (d.source.x + d.target.x) / 2;
		}).attr("y", function(d) {
			return (d.source.y + d.target.y) / 2;
		})
	});
});
