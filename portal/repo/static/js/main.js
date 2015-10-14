
 var dataValues =[{
	"id":1, 	"text":"QARepositoiese", "iconCls":"icon-site",
	"children":[{"id":9, "text":"repo","iconCls":"icon-repo"},
	{"id": 6, "text": "cRepo", "iconCls":"icon-com-repo"},
	{ 
		"id":3, 		"text":"3rdParty",	"state":"open", 		"iconCls":"icon-folder",
		"children":[{"id":4, "text":"allasians",	"iconCls":"icon-repo"},
		{"id": 8, "text":"CC", "iconCls":"icon-repo"}]
	}]
	},{
	"id": 2,
	"text":"webtools",
	"state":"closed", "iconCls":"icon-site",
	"children":[{"id": 5, "text":"Java", 	"iconCls":"icon-com-repo"},
	{"id": 6, "text": "esfjet", "iconCls":"icon-com-repo"}]
}];

var currentNode=null;
var allRepos = new Array();
function handleNode(ele){
	$.each(ele,function(index,ele){
		if(ele.type){
			if(ele.type =="S"){
				ele.iconCls ="icon-site";
				ele.state="open";
			}
			if(ele.type =="C"){
				ele.iconCls ="icon-com-repo";
				ele.state="close";
			}

			/*if(ele.type =="F"){
				ele.iconCls ="icon-folderclosed";
				ele.state="close";
			}*/
			if(ele.type =="R"){
				ele.iconCls ="icon-repo";
				ele.state="close";
				allRepos.push(ele);
			}
			delete ele.type;
		}else{
			ele.iconCls ="icon-site";
			ele.state="open";
		}
		if(ele.children){
			handleNode(ele.children);
		}
	});
}
function loadDataForTree(){
	$.ajax({     
		type: "GET",  
		url:  "/nodes/?radom=" +Math.random(),  
		cache: false,  
		async:false,  
		dataType :'json',
		data:"",
		success:function(data){ 
			var sourceJson = data;
			allRepos = new Array();
			handleNode(sourceJson);
			dataValues = sourceJson;
			$('#tt').tree('loadData', dataValues);	
		}
	});
}

function goHome(){
	if(currentNode != null)
		$(currentNode.target).removeClass("tree-node-selected");
	currentNode = null;
	$("#workspace").attr("src","/static/home.html");
}
function goCategoryConfigurePage(){
	$("#workspace").attr("src", "/static/category.html");
}
function gotoNode(targetNodeId){
	targetNode = $("#tt").tree("find", targetNodeId);
	targetNode.target.click();
}
function findNodeParent(nodeId){
	var array =new Array();
    node = $("#tt").tree("find", nodeId);
	array.push(node);
	var parentNode = $("#tt").tree("getParent",node.target);
	while(parentNode){
	    array.push(parentNode);
		parentNode = $("#tt").tree("getParent",parentNode.target);
	}
    return array;
}
function findNodeChildren(nodeId){
	node = $("#tt").tree("find", nodeId);
	var childrenNodes = $("#tt").tree("getChildren",node.target);
	return childrenNodes;
}
function findNode(id){
	return $('#tt').tree('find',id);
}
function getPath(node,hideHyperLink){
    var array =new Array();
    array.push(node);
	var parentNode =$('#tt').tree("getParent",node.target);
	while(parentNode){
	     array.push(parentNode);
	     parentNode =$('#tt').tree("getParent",parentNode.target);
	}
    var result = "";
    for(var i =array.length-1; i>=0; i--){
	    if(!hideHyperLink){
			result +="<a href='javascript:parent.gotoNode("+array[i].id+")'>"+ array[i].text +"</a>";
		}else{
		    result += array[i].text;
		}
		if(i !=0){
		   result +="->";
		}
	}
	return result;
}

function createSite(){
    var sitename =  $("#c-siteName").val();
    var hidden =  $("#c-hide").prop("checked");
    var hiddenStr ="";
    if(hidden) hiddenStr = "&hidden=on";
	var pattern = /^\w+$/;
	if(sitename=="" || !pattern.test(sitename)){
		var message = 'The name should be number, char or underscore, please input it again!';
		$.messager.alert("Illegal Site Name", message, "info");
		return;
	}
	//check if exist
	if(checkSiteExists(sitename)){
		$.messager.alert("Site Exist", "The site has already existed. Please input another site name.", "info");
		return;
	}
	$("#createSDlg").modal('hide');
	showLoading();
	$.ajax({     
		type: "POST",  
		url:  "/sites/",
		cache: false,  
		async:false,  
		dataType :'*',
		data:"name="+sitename+hiddenStr,
		success:function(data){
			loadDataForTree();
			hideLoading();
			gotoNode(data.id);
//			$("#createSDlg").modal('hide');
			$.messager.show({
				title:'Success',
				msg:'Create site successfully',
				timeout:4000,
				showType:'slide'
			});
			
	   },
       error:function(data,status,e){
    	   hideLoading();
    	   $.messager.alert('Failed','Create site failed. Please try it later.','error');
		}
	});
}
function checkSiteExists(siteName){
	var sites = getAllSites();
	for(var i=0; i<sites.length;i++){
		var site = sites[i];
		if(site["name"] == siteName){
			return true;
		}
	}
	return false;
}
function deleteSite(){
	//check refer
	var siteId = $("#deleteSel").val();
	$("#deleteSDlg").modal('hide');  //close delete dialog
	showLoading();
	doBeforeCheckSiteReferrence(siteId, sendDeleteReq);
}
function sendDeleteReq(){
	var siteId = $("#deleteSel").val();
	
	$.ajax({     
		type: "DELETE",  
		url:  "/site/"+siteId+"/",
		cache: false,  
		async:false,  
		dataType :'*',
		data:"",
		success:function(data){  
			loadDataForTree();    //refresh tree
			hideLoading();
			goHome();
			
			$.messager.show({
				title:'Success',
				msg:'Delete the site successfully',
				timeout:4000,
				showType:'slide'
			});
	   },
		error:function(data,status,e){
			hideLoading();
			$.messager.alert('Failed',"Delete this site failed. Please try it later.",'error');
		}
  });
}
function syncSites(){
	//valid
	var sourceId = $("#sourceSel").val();
	var destId = $("#destSel").val();
	if(sourceId == destId){
		$.messager.alert("Information", "Source Site and Destine Site can't be the same one.", "info");
		$("#destSel").focus();
		return;
	}
	$("#syncSDlg").modal("hide");//close sync dialog
	showLoading();
	//check refer
	doBeforeCheckSiteReferrence(destId, sendSyncReq);
}
function sendSyncReq(){
	var sourceId = $("#sourceSel").val();
	var destId = $("#destSel").val();
	
	$.ajax({     
			type: "POST",  
			url:  "/site/"+sourceId+"/synchronise/",
			cache: false,  
			async:false,  
			dataType :'*',
			data:"destination="+destId,
			success:function(data){  
				loadDataForTree();
				hideLoading();
				
				goHome();
				$.messager.show({
					title:'Success',
					msg:'Synchronize is successful',
					timeout:4000,
					showType:'slide'
				});
				
		   },
			error:function(data,status,e){
				hideLoading();
			   $.messager.alert('Failed',"Synchronization Failed",'error');
			}
	  });
}
function recoverSite(){
	//check refer
	var siteId = $("#recoverSel").val();
	$("#recoverSDlg").modal("hide");//close recover dialog
	showLoading();
	doBeforeCheckSiteReferrence(siteId, sendRecoverReq);
}

function sendRecoverReq(){
	var siteId = $("#recoverSel").val();
	$.ajax({     
		type: "POST",  
		url:  "/site/"+siteId+"/recover/",
		cache: false,  
		async:false,  
		dataType :'*',
		data:"  ",
		success:function(data){  
			hideLoading();  //refresh tree
			loadDataForTree(); 
			goHome();
			
			$.messager.show({
				title:'Success',
				msg:'Rollback is successful',
				timeout:4000,
				showType:'slide'
			});

	   },
		error:function(data,status,e){
		   data  =retrieveData(data.responseText,"POST", "</pre>","\""); 
		   var pos = data.indexOf("POST");
		   var pos1 = data.indexOf("</pre");
		   data = data.replace(/\"/g,"");
		   if(pos !=-1 && pos1 !=-1){
		      data = data.substring(pos+4,pos1).Trim();
		   }
		   hideLoading();
		   $.messager.alert('Failed',"Rollback Failed: " +data,'error');

		}
  });	
}

function getAllSites(){
	var sites = [];
	var nodes = $("#tt").tree('getRoots');
	for(var i=0; i<nodes.length;i++){
		var siteId = nodes[i].id;
		var siteName = nodes[i].text;
		sites.push({"id": siteId, "name":siteName});
	}
	return sites;
}

function loadSites(selControl, sites){
	for(var i=0; i<sites.length; i++){
		site = sites[i];
		selControl.append("<option value='"+ site["id"]+"' >"+site["name"]+"</option>");
	}
}

function doBeforeCheckSiteReferrence(siteId, callbackFunc){
    // check whether the repos in siteId are referred by other repos
	showLoading();
    $.ajax({
 	  type: "GET",
 	  url: "/site/"+siteId+"/checkreference",
 	  cache: false,
 	  async: false,
      dataType: "json",
      success: function(dt){
    	  hideLoading();
    	  //{'flag': , 'data':[]}
    	  if(dt.flag == true){
    			$.messager.alert("Information", "The repos in this site are referred by site: " + dt.data 
    					+ " . Please release those referrences before this operation.", "info");
    		
    	  }else{
    			callbackFunc();
    	  }
      }, 
      error:function(data,status,e){
    	$.messager.alert("Information", "Error in Server. Please try it later.", "info");
      }
    });
}

function checkNameExistInNode(node, name){
	var subNodes = $("#tt").tree('getChildren', node.target);
	for(var i=0;i<subNodes.length;i++){
		var subNode = subNodes[i];
		var parent = $("#tt").tree('getParent', subNode.target);
		if(parent.id == node.id && name==subNode.text)
			return true;
	}
	return false;
}

function getRepoNum(node){
	var subNodes = $("#tt").tree('getChildren', node.target);
	var count = 0;
	for(var i=0; i<subNodes.length;i++){
		var subNode=subNodes[i];
		if(subNode.iconCls == "icon-repo"){
			count++;
		}
	}
	return count;
}

function getCompositeNum(node){
	var count = 0;
	var subNodes = $("#tt").tree('getChildren', node.target);
	for(var i=0; i<subNodes.length;i++){
		var subNode=subNodes[i];
		if(subNode.iconCls == "icon-com-repo"){
			count++;
		}
	}
	return count;
}


function logout(){
	  $.ajax({
		  type: "GET",  
			url:  "/logout/",
			cache: false,  
			async:false,  
			dataType :'json',
			data:"",
			success: function(data){
				document.location.href = data.url
			},
			error:function(data,status,e){
				$.messager.alert('Logout Failed',data,'error');
			}
		  
	  })
}

function checkUserIdentity(){
	$.ajax({     
		type: "GET",  
		url:  "/user/",  
		cache: false,  
		async:false,  
		dataType :'json',
		data:"",
		success:function(data){ 
			if(data.is_superuser == true)
			{
				$('#siteOperDiv').show();
			}else
			{
				$('#siteOperDiv').hide();
			}
	   },
	   error:function(data,status,e){
		   $('#siteOperDiv').hide();
		}
	 });
}

