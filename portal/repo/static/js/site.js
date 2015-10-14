
function loadRepos(dg){
	$.ajax({     
		type: "GET",  
		url:  "/repositories/",  
		cache: false,  
		async:false,  
		dataType :'json',
		data:"",
		success:function(data){ 
			reposData = data;
			dg.datagrid('loadData',reposData);			  
	   }
	 });
}

function cleanRepoInfo(){
	$("#repoName").val(undefined);
	$("#description").val(undefined);
}

function cleanComInfo(){
	$("#comRepoName").val(undefined);
}

function checkRepoInfo(){
	var name = $("#repoName").val();
	var pattern = /^\w+$/;
	if(!name || name=="" || !pattern.test(name)){
	   $.messager.alert('Illegal name','The name should be number, char or underscore, please input it again!','error');
	   return false;
	}
	
	var description = $("#description").val();
	if(!description || description==""){
		$.messager.alert('Add Repository','The description is required!','error');
		return false;
    }
	return true;
}


function addRepo(){
	if(!checkRepoInfo())
		return;
	var name = $("#repoName").val();
	if(parent.checkNameExistInNode(treeNode,name)){
		$.messager.alert("Warning","The name of "+ name +" is already in use. Please choose another one."
				,"warn");
		return;
	}
	showLoading();
	var description = handleSpecialChar($("#description").val());
	var param = "text="+name+"&parent="+treeNode.id+"&type=R&description="+description;
	var nodeId = -1;
	//add
	$.ajax({     
		type: "POST",  
		url:  "/nodes/",
		cache: false,  
		async:false,  
		dataType :'json',
		data:param,
		success:function(data){  
			
			nodeId = data.id;		
			parent.loadDataForTree();
			hideLoading();
			parent.gotoNode(nodeId);
	   },
		error:function(data,status,e){
			hideLoading();
			if(e=='FORBIDDEN'){
			$.messager.alert('Create Failed',"You don\'t have such permisson.",'error');
		    }else {
		    	$.messager.alert('Create Failed','Create Failed','error');
		    }
			
		}
	});
}

function checkComInfo(){
	var name = $("#comRepoName").val();
	var pattern = /^\w+$/;
	if(!name || name=="" || !pattern.test(name)){
	   $.messager.alert('Illegal name','The name should be number, char or underscore, please input it again!','error');
	   return false;
	}
	return true;
}

function addComposite(){
	if(!checkComInfo())
		return;
	
	var name = $("#comRepoName").val();
	if(parent.checkNameExistInNode(treeNode,name)){
		$.messager.alert("Warning","The name of "+ name +" is already in use. Please choose another one."
				,"warn");
		return;
	}
	showLoading();
	var param = "text="+name+"&parent="+treeNode.id+"&type=C";
	//add node
	$.ajax({     
		type: "POST",  
		url:  "/nodes/",
		cache: false,  
		async:false,  
		dataType :'json',
		data:param,
		success:function(data){  
			nodeId = data.id;		
			parent.loadDataForTree();
			hideLoading();
			parent.gotoNode(nodeId);
	   },
		error:function(data,status,e){
			hideLoading();
			if(e=='FORBIDDEN'){
			$.messager.alert('Create Failed',"You don\'t have such permisson.",'error');
	         }else {
	    	$.messager.alert('Create Failed','Create Failed','error');
	       }
		}
	});
	
}