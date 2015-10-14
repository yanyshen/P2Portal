
/*if(parent.currentNode == null)
{	
		parent.goHome();
}*/

String.prototype.Trim = function() {
	return this.replace(/(^\s*)|(\s*$)/g, "");
}
String.prototype.LTrim = function() {
	return this.replace(/(^\s*)/g, "");
}
String.prototype.RTrim = function() {
	return this.replace(/(\s*$)/g, "");
}

Array.prototype.contains = function(obj) {
	var i = this.length;
	while (i--) {
		if (this[i] == obj) {
			return true;
		}
	}
	return false;
}

function organizePath(){
	
	array = parent.findNodeParent(parent.currentNode.id);
    while(array.length > 1){
        node = array.pop();
        $("#path").append("<li><a href='#' onClick='parent.gotoNode("+node.id+")'>"+node.text+"</a> <span class='divider'>/</span></li>");     
    }
    node = array.pop();
    $("#path").append("<li class='active'>"+node.text+"</li>");
}
//if the return data is html format, it needs to retrieve data from html text.
function retrieveData(data,startTag, endTag, quote,needPrefix){
	var result = data; ;
	if(!startTag) startTag = "[";
	if(!endTag) endTag = "]";
	if(!quote) quote = "'";
	var posFrom =data.indexOf("<html");
	if(posFrom ==-1){
		posFrom =data.indexOf("<DIV");
	}
	if(posFrom>-1){
		data = data.substring(posFrom);
		// replace the html encode characters 
		data = data.replace(/&lt;/g,"<");
		data = data.replace(/&gt;/g,">");
		data = data.replace(/&quot;/g,quote);
		var pos =data.indexOf(startTag);
		 
		if(  pos >-1){
			var pos1 = data.indexOf(endTag);
			result   = data.substring(pos,pos1+endTag.length);
			if(needPrefix){
				result ="\"" + result +"\"";
			}
		}
	}
	return  result;
}
function retrieveArrByTag(data,beginTag,endTag,quote){
    var firstPos=   data.indexOf(beginTag);
    var secondPos = data.indexOf(endTag);
    if(firstPos >=secondPos){
    	return data;
    }
    data  =retrieveData(data,beginTag, endTag,quote); 
    var pos = data.indexOf(beginTag);
    var pos1 = data.indexOf(endTag);
    if(pos !=-1 && pos1 !=-1){
    	data = data.substring(pos+beginTag.length,pos1).Trim();
    }
    return data;	   
}

function retrieveArr(data,beginTag,endTag,quote){
     data = retrieveArrByTag(data,beginTag,endTag,quote);
     data = retrieveArrByTag(data,"POST",endTag,quote);
     data = retrieveArrByTag(data,"GET",endTag,quote);
     data = retrieveArrByTag(data,"DELETE",endTag,quote);
     return data;
}

// if  the char contains like "c:\test", the request can not be sent. This function convert "c:\test " to "c:/test"
function handleSpecialChar(obj){
	obj = encodeURIComponent(obj);
	obj  =obj.replace(/\%5C/g,"%2F")
	obj = decodeURIComponent(obj);		
		        obj =obj.replace(/(\r\n|\r|\n)/g, '\\n')
	return obj.Trim();
}

function stringify(obj) {
    var json = [];
    parse(obj,json);
    return ( String(json));
};


function parse(obj,json,parentTag){
	var t = typeof (obj);
	if (t != "object" || obj === null) {
		// simple data type
		if (t == "string"){
			json.push(String(obj)+"\n");
		}
	}
	else {
		// recurse array or object
		var n, v, arr = (obj && obj.constructor == Array);
		for (n in obj) {
			v = obj[n]; t = typeof(v);
			if(t == "function") continue;
			if (t == "object" && v !== null){
				v = parse(v,json,n);
			}
			if(arr){
				json.push(parentTag+":"+String(v)+"\n");
			}
		}
	}		
}

//translate error message
function json2String(data,beginTag){
   if(data.status ==500){
      return data.statusText;
   }
   var tag = "POST";
   if(beginTag){
     tag = beginTag
   }
   var result = retrieveArr(data.responseText,tag,"</pre>");
   result = retrieveArr(result,"POST","</pre>");
   result = retrieveArr(result,"DELETE","</pre>");
           result = retrieveArr(result,"GET","</pre>");
   var jsonData =eval("("+result+")"); 

   return stringify(jsonData);
}


function buildOperationJson(data, length){
		if(!length) 
			length =22;
	
	var jsonData =data; 
	$.each(jsonData,function(index,ele){
		if(ele.type=="M"){
			ele.way ="Mirror";
		}else if(ele.type=="P"){
		  	ele.way = "Publish";
		}else if(ele.type=="R"){
			ele.way ="Rollback";
		}else if(ele.type=="S"){
		    ele.way ="System";
		}else if(ele.type=="C"){
			ele.way = "Cleanup"
		}

        if(ele.commit_time){
			ele.commit_time = ele.commit_time.substring(0,length);
		}
		   
		if(ele.repository_id){
			var node =  parent.findNode(ele.repository_id);
			if(!node){
				ele.repo = "hidden"
			}else{
				var path =  parent.getPath(node);
				ele.repo = path;
			}
		}

	});
	return jsonData;
}

function filterURL(url){
	 var pos = url.indexOf("<a");
	if(pos !=-1){
	    pos = url.indexOf(">");
		url =url.substring(pos+1);
		pos = url.indexOf("<");
		url = url.substring(0,pos);
	}
	return url;
}


function buildRepoMirrorURLForCombo(mirrorUrlCombo){
	$.ajax({     
		type: "GET",  
		url:  "/repositories/",  
		cache: false,  
		async:false,  	
		dataType :'json',
		data:"",
		success:function(data){ 
		    reposData = data;
		    var jsonData = [];
			for(var i= 0; i<reposData.length;i++){
				var repo = reposData[i];
				if(treeNode.id == repo.id)
					continue;
				jsonData.push({"id": repo.id, "text": repo.name+' (Path:'+repo.site+'->'+repo.path+')'});
			  }
			mirrorUrlCombo.combobox('loadData', jsonData);			
	   }
	 });

}

function showLoading(){
	parent.showLoading();
}
function hideLoading(){
	parent.hideLoading();
}

//format output string of features details
function formatOutputString(obj){
     var arr = obj.toString().split(",");
	 var output = "";
	 for( var i = 0; i<arr.length;i++){
	    output +=arr[i]+"<br>";
	 }
	 return output;
}
