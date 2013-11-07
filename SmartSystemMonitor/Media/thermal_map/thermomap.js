var MAX_TEMP_SYS = 65;
var MIN_TEMP_SYS = 15;

var floatToColor = function(temp){
	var colors = ['#ff1717', '#ff1212', '#ff0e0e', '#ff0b0b', '#ff0808', '#ff0606', '#ff0505', '#ff0303', '#ff0202', '#ff0202', '#ff0101', '#ff0101', '#ff0000', '#ff0000', '#ff0000', '#ff0000', '#ff0000', '#ff0000', '#ff0000', '#ff0000', '#ff0100', '#ff0400', '#ff0600', '#ff0a00', '#ff0e00', '#ff1200', '#ff1600', '#ff1a00', '#ff1f00', '#ff2400', '#ff2900', '#ff2d00', '#ff3300', '#ff3900', '#ff3e00', '#ff4400', '#ff4a00', '#ff5100', '#ff5600', '#ff5d00', '#ff6300', '#ff6900', '#ff6f00', '#ff7600', '#ff7c00', '#ff8300', '#ff8900', '#ff9000', '#ff9600', '#ff9c00', '#ffa300', '#ffa900', '#ffaf00', '#ffb500', '#ffbb00', '#ffc000', '#ffc600', '#ffcb00', '#ffd000', '#ffd500', '#ffda00', '#ffde00', '#ffe300', '#ffe800', '#ffeb00', '#ffee00', '#fff200', '#fff500', '#fff700', '#fffa00', '#fffb00', '#fdfc00', '#fafc01', '#f8fc02', '#f4fc02', '#f1fc03', '#edfc03', '#e9fc03', '#e5fc04', '#e1fc04', '#dcfc05', '#d8fc05', '#d3fc06', '#cefc07', '#c9fc07', '#c5fc08', '#bffb08', '#b9f909', '#b4f709', '#aef60a', '#a9f40b', '#a4f20b', '#9ef00c', '#97ee0d', '#92ec0e', '#8ce90e', '#86e70f', '#80e410', '#7ae211', '#74df12', '#6edd13', '#69da14', '#63d815', '#5dd616', '#58d317', '#52d118', '#4ccf19', '#47cc1a', '#42ca1c', '#3cc81e', '#37c61f', '#32c421', '#2dc222', '#28bf23', '#24be25', '#1fbc27', '#1bbb28', '#17b92b', '#13b82c', '#0fb72e', '#0cb630', '#09b533', '#06b535', '#03b437', '#01b439', '#00b43c', '#00b43e', '#00b441', '#00b544', '#00b646', '#00b64a', '#00b74d', '#00b850', '#00b854', '#00ba58', '#00bb5c', '#00bc5f', '#00be63', '#00bf68', '#00c16c', '#00c270', '#00c474', '#00c678', '#00c87d', '#00c981', '#00cb86', '#00cd8a', '#00cf8f', '#00d193', '#00d397', '#00d59c', '#00d7a0', '#00d8a5', '#00dbab', '#00deb2', '#00e0b8', '#00e3be', '#00e5c5', '#00e7cb', '#00e9d1', '#00ead6', '#00eadc', '#00eae1', '#00eae6', '#00eaea', '#00eaee', '#00eaf2', '#00eaf6', '#00eaf8', '#00eafb', '#00eafe', '#00eaff', '#00e8ff', '#00e4ff', '#00e0ff', '#00dbff', '#00d6fe', '#00d0fc', '#00cafa', '#00c3f7', '#00bcf4', '#00b4f0', '#00adec', '#00a4e8', '#009ce4', '#0093de', '#008bda', '#0082d5', '#007ad0', '#0075cd', '#0070cb', '#006bc7', '#0063c4', '#005dc1', '#0056bd', '#004eb8', '#0047b4', '#0041af', '#003aab', '#0034a7', '#002ea2', '#00289d', '#002398', '#001e93', '#001a8e', '#001688', '#001283', '#000f7e', '#000c78', '#000973', '#01086e', '#01066a', '#010565', '#020461', '#03045c']//, '#040559', '#050555', '#060652', '#07074f', '#08084d', '#0a0a4d', '#0c0c4d', '#0e0e4c', '#10104a', '#131349', '#151548', '#181847', '#1a1a45', '#1d1d46', '#202045', '#232344', '#252543', '#282843', '#2a2a41', '#2c2c41', '#2e2e40', '#30303f', '#31323e'];
	var value = Math.ceil((temp-MIN_TEMP_SYS)/(MAX_TEMP_SYS-MIN_TEMP_SYS)*colors.length);
	//console.log(value);
	return colors[Math.min(colors.length-1, Math.max(colors.length-value, 0))];
}

function previewUrl(url,target){
    clearTimeout(window.ht);
    clearTimeout(window.closeht);
    window.ht = setTimeout(function(){
        //var div = document.getElementById(target);
    	$(target).show();
        $(target).html('<iframe style="width:100%;height:100%;" frameborder="0" src="' + url + '" />');
    },20);
}

var createBoard = function(width, height, container){
    var board = $(container);
    var lines = [];
    for(var i = 0; i < height; i++){
        lines[i] = [];
        for(var j = 0; j < width; j++){
            lines[i][j] = $("<div class='frame'></div>");
            board.append(lines[i][j]);
        }
        board.append($("<div class='separator'></div"));
    }
    return lines;           
}

var ThermoMap = function(width, length, container, layer, minTemp, maxTemp){
	createBoard(width, length, "#board");
	MAX_TEMP_SYS = +maxTemp;
	MIN_TEMP_SYS = +minTemp;
	this.racks = [];
	this.motes = [];
	this.width = width;
	this.length = length;
	this.container = $(container);
	this.layer = $("#border_layers");
	
	this.addRack = function(x,y,z,width, length, height, label){
		var top = Math.ceil(this.container.offset().top+ y*this.container.height()/this.length);
		var left = Math.ceil(this.container.offset().left+x*this.container.width()/this.width);
		var width = Math.ceil(this.container.width()*width/this.width);
		var height = Math.ceil(this.container.height()*length/this.length);
		
		var rack = $("<div class='rack'><p class='content'>"+label+"</p></div>");
		rack.css({'top': top+"px", 'left':left+"px", 'width': width+"px", "height":height+"px"});
		this.layer.append(rack);
		this.racks.push(rack);
	}
	
	this.addMote = function(x,y,z, temp, id){
		//console.log(temp);
		var temp = temp.toFixed(1);
		var open_url = "onclick= \"window.location.href='../";
		//console.log(open_url+id)
		for(var m = 0; m < this.motes.length; m++){
			if((x == +this.motes[m].x) && (y == +this.motes[m].y)){
				this.motes[m].temps[z] = {z:z, id:id, temp:temp};
				var contents = this.motes[m].contents;
				contents.empty();
				var maxTemp = -Infinity, maxTempI = 0;
				for(var i = 0; i < this.motes[m].temps.length; i++){
					var temp_obj = this.motes[m].temps[i];
					if(temp_obj){
						var colored_mark = "<div class='min_mote' style='background-color:"+floatToColor(temp_obj.temp)+"'></div>";
						var line = $("<div id='c"+i+"' class='content_temp_item' "+open_url+temp_obj.id+"'\">" +
								     "<a href='#'>ID:"+temp_obj.id+" :&nbsp;"+colored_mark+"&nbsp;"+temp_obj.temp+"°</a></div>");
						contents.prepend(line);
						if(+temp_obj.temp > maxTemp){
							maxTemp = temp_obj.temp;
							maxTempI = i;
						}
					}
				};
				$($(contents).find("#c"+maxTempI)).css({"font-weight": "bold"});
				this.motes[m].css({"background-color":floatToColor(maxTemp)});
				this.motes[m].balloon({contents:contents, position:"top"})
				return;
			}
		}
		var mote = $("<div class='mote'></div>");
		var colored_mark = "<div class='min_mote' style='background-color:"+floatToColor(temp)+"'></div>";
		mote.x = x;
		mote.y = y;
		mote.temps = [];
		mote.temps[z] = {z:z, id:id, temp:temp};
		mote.id = id;
		mote.contents = $("<div class='content_temp_balloon'></div>");
		var line = $("<div class='content_temp_item' "+open_url+id+"'\" style='font-weight:bold'><a href='#'>ID:"+id+" :&nbsp;"+colored_mark+"&nbsp;"+temp+"°</a></div>");
		mote.contents.prepend(line);
		mote.css({"background-color":floatToColor(temp)});
		this.layer.append(mote);
		var top = Math.ceil(this.container.offset().top+ y*this.container.height()/this.length - mote.height()/2);
		var left = Math.ceil(this.container.offset().left+x*this.container.width()/this.width - mote.width()/2);
		mote.css({'top': top+"px", 'left':left+"px"});
		$(mote).balloon({contents:mote.contents, position:"top", css: {minWidth: "20px"}});
		this.motes.push(mote);
	}
}