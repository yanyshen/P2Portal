var categoryData = {};
//data example --<
categoryData = {'com.category.a': {label:'aaa', description:'aaaaa',features:{"com.feature.a":"path","com.feature.b":"path"}}, 
				'com.category.b': {label:'bbb', description:'bbbbb',features:{"com.feature.a":"path","com.feature.b":"path"}},
				'com.category.c': {label:'aaa', description:'aaaaa',features:{"com.feature.a":"path","com.feature.b":"path"}}, 
				'com.category.d': {label:'aaa', description:'aaaaa',features:{"com.feature.a":"path","com.feature.b":"path"}}, 
				'com.category.e': {label:'aaa', description:'aaaaa',features:{"com.feature.a":"path","com.feature.b":"path"}}, 
				'com.category.f': {label:'aaa', description:'aaaaa',features:{"com.feature.a":"path","com.feature.b":"path"}}
};
//data example -->
var featureData = [{"path":"", "name":"", "version":"","commit_time":"", "committer":""}]
var updateFlag=false;

function loadFeature(){
	$.ajax({     
		type: "GET",  
		url:  "/repository/"+treeNode.id+"/feature/",  
		cache: false,  
		async:false,  
		dataType :'json',
		data:"",
		success:function(result){
			featureData = result.rows;
			sortFeature("commit_time", "desc");
			//data = {"rows":featureData};
			$("#tFeature").datagrid('loadData', featureData);
		}
	});	
}

function loadCategory(){
	$.ajax({     
		type: "GET",  
		url:  "/repository/"+treeNode.id+"/category/",  
		cache: false,  
		async:false,  
		dataType :'json',
		data:"",
		success:function(result){
			categoryData = result;
			var dgData = [];
			for(key in categoryData){
				var ct_id = key;
				var ct_name = categoryData[key].label;
				var ct_description = categoryData[key].description;
				var operation = organizeOperations(ct_id);
				dgData.push({"ct-id":ct_id, "ct-name":ct_name, "ct-desc":ct_description, "operation":operation});
			}
			$("#t-category").datagrid('loadData', dgData);
		} 
	});
}

function organizeOperations(categoryId){
	var str = "<a style='margin-right:5px' class='btn btn-success' href='javascript: showViewBox(\""+categoryId+"\")' ><i class='icon-zoom-in icon-white'></i> View </a>";
	str += "<a style='margin-right:5px' class='btn btn-info' href='javascript: showEditBox(\""+categoryId+"\")' ><i class='icon-edit icon-white'></i> Edit </a>";
	str += "<a class='btn btn-danger' href='javascript: deleteCategory(\""+categoryId+"\")'><i class='icon-trash icon-white'></i> Delete</a>";
	return str
}
var addFlag = false;
var beforeEditData = {} 	
function showEditBox(categoryId){
	//set edit flag
	addFlag = false;
	
	//clean 
	clearDetailedBox();
	//show detailed information box
	$("#detail").panel('open');
	//show confirm button
	$("#confirmBtn").show();
	//set information
	$("#id").val(categoryId);
	$("#name").val(categoryData[categoryId].label);
	$("#description").val(categoryData[categoryId].description);
	
	//check features
	categoryValue = categoryData[categoryId];
	features = categoryValue.features;
	for(key in features){
		var rowIndex = $("#tFeature").datagrid('getRowIndex', features[key]);
		$("#tFeature").datagrid('checkRow', rowIndex);
	}
	beforeEditData[categoryId] = categoryData[categoryId];
}
//check if user modify category
function checkModify(categoryId, name, description, features){
	if(beforeEditData && categoryId in beforeEditData)
	{
		//categoryId is not changed.
	}
	else
		return true;
	if(beforeEditData[categoryId].label != name)
		return true;
	if(beforeEditData[categoryId].description != description)
		return true;
	for(key in features){
		if(beforeEditData["features"] && key in beforeEditData["features"]){
			//
		}else{
			return true;
		}
	}
	for(key in beforeEditData["features"]){
		if(key in features){
			//
		}else{
			return true;
		}
	}
	$.messager.alert("Information", "No information has been modified for this category", "info");
	return false;
}
//check required items 
function checkRequired(){
	var id = $("#id").val();
	if(!id || id == ""){
		$.messager.alert("Information", "Category id can not been none.", "info");
		return false;
	}
	var name = $("#name").val();
	if(!name || name == ""){
		$.messager.alert("Information", "Category name can not been none.", "info");
		return false;
	}
	var rows = $("#tFeature").datagrid('getChecked');
	if(rows.length == 0){
		$.messager.alert("Information","Features should be specified for category", "info");
		return false;
	}
	return true;
}
//check id unique
function checkIdUnique(){
	var id=$("#id").val();
	if(!addFlag&&!$.isEmptyObject(beforeEditData)){
		//modify
		if(id in categoryData){
			if(id in beforeEditData){
				
			}else{
				//id has been modify to an existing id in categoryData
				return false;
			}
		}
	}else if(addFlag){
		//add
		if(id in categoryData)
			return false;
	}
	return true;
}

function save(){
	if(!checkRequired())
		return;
	if(!checkIdUnique())
		return;
	var id=$("#id").val();
	var name=$("#name").val();
	var description = $("#description").val();
	var rows = $("#tFeature").datagrid('getChecked');
	features = {};
	for (var i=0;i<rows.length;i++){
		key = rows[i].name+"("+rows[i].version+")";
		value = rows[i].path;
		features[key]=value;
	};
	if(!addFlag && !$.isEmptyObject(beforeEditData) && checkModify(id, name, description, features)){
		//edit modify category table
		var oldId;
		for(key in beforeEditData){
			oldId = key;
			break;
		}
		var rowIndex = $("#t-category").datagrid('getRowIndex', oldId);
		var operationStr = organizeOperations(id);
		$("#t-category").datagrid('updateRow', {
			index: rowIndex,
			row: {
				"ct-id": id,
				"ct-name": name,
				"ct-desc": description,
				"operation":operationStr
			}
		});
		
		//save to categoryData
		if(oldId != id){
			delete categoryData[oldId];
		}
		categoryData[id]={label:name, description:description,features:features};
			
	}else if(addFlag){
		//add: append row
		var operationStr = organizeOperations(id);
		$("#t-category").datagrid('appendRow', {
			"ct-id": id,
			"ct-name": name,
			"ct-desc": description,
			"operation": operationStr
		});
		
		//save to categoryData
		categoryData[id]={label:name, description:description,features:features};
	}
	updateFlag = true;
	$("#detail").panel('close');
}

function showViewBox(categoryId){
	//clean 
	clearDetailedBox();
	//show detailed information box
	$("#detail").panel('open');
	//hide confirm button
	$("#confirmBtn").hide();
	//set information
	$("#id").val(categoryId);
	
	$("#name").val(categoryData[categoryId].label);
	$("#description").val(categoryData[categoryId].description);
	
	//check features
	categoryValue = categoryData[categoryId];
	features = categoryValue.features;
	for(key in features){
		var rowIndex = $("#tFeature").datagrid('getRowIndex', features[key]);
		$("#tFeature").datagrid('checkRow', rowIndex);
	}
	
	//set readonly 
	$('input').attr("readonly",true);
	$("textarea").attr("readonly",true);
}

function clearDetailedBox(){
	//set information
	$("#id").val(undefined);
	$("#name").val(undefined);
	$("#description").val(undefined);
	$('input').removeAttr("readonly");
	$("textarea").removeAttr("readonly");
	$("#tFeature").datagrid('uncheckAll');
}

//name, version, commit_time, committer;asc, desc
function sortFeature(sort, order){
	var flag = true;
	if(order=="desc")
		flag = false;
	if(sort=="name"){
		featureData.sort(function(a,b){
			if(a.name<b.name && flag)
				return true;
			if(a.name>b.name && !flag)
				return  true;
			return false;
		});
	}
	if(sort=="version"){
		featureData.sort(function(a,b){
			if(a.version<b.version && flag)
				return true;
			if(a.version>b.version && !flag)
				return  true;
			return false;
		});
	}
	if(sort=="commit_time"){
		featureData.sort(function(a,b){
			// both of a and b's commit time is unknown 
			if(a.commit_time == "unknown" && b.commit_time == "unknown")
				return true;
			else if(a.commit_time == "unknown")  //a's commit time is unknown and b's known
				return false;
			else if(b.commit_time == "unknown")   //a's known but b's unknown
				return true;
			//both of a and b's commit time is known
			date1 = new Date(Date.parse(a.commit_time));
			date2 = new Date(Date.parse(b.commit_time));
			if(date1<date2 && flag)
				return true;
			if(date1>date2 && !flag)
				return  true;
			return false;
		});
	}
	if(sort=="committer"){
		featureData.sort(function(a,b){
			if(a.committer<b.committer && flag)
				return true;
			if(a.committer>b.committer && !flag)
				return  true;
			return false;
		});
	}
	
}

function showAddBox(){
	//set edit flag
	addFlag = true;
	
	//clean 
	clearDetailedBox();
	//show detailed information box
	$("#detail").panel('open');
	//show confirm button
	$("#confirmBtn").show();
}
function deleteCategory(categoryId){
	$.messager.confirm('Confirm', 
	 		 'Are you sure to delete this category?', 
			 function(r){
			 	 if(r){
					 updateFlag = true;
					 delete categoryData[categoryId];
					 var rowIndex = $("#t-category").datagrid('getRowIndex', categoryId);
					 $("#t-category").datagrid('deleteRow', rowIndex);
					 if($("#id").val()==categoryId){
						 $("#detail").panel('close');
					 }
				 }
			 }
	 );
}

function publishCategory(){
	if(!updateFlag)
	{
		$.messager.alert("Information", "No change on category information needs to republish.", "info");
		return;
	}
	if($("#t-category").datagrid('getRows').length==0)
	{
		$.messager.alert("Information", "No category needs to publish.", "info");
		return;
	}	
	showLoading();
	$.ajax({     
		type: "POST",  
		url:  "/repository/"+treeNode.id+"/category/",
		cache: false,  
		async:false,  
		dataType :'html',
		data:"category="+JSON.stringify(categoryData),
		success:function(data){ 
			hideLoading();
			$.messager.confirm('Success', 
			 		 'Publish category successfully. Return to repository page?', 
					 function(r){
					 	 if(r){
					 		parent.gotoNode(treeNode.id);
					 	 }
			});
		},
		error:function(data,status,e){
			hideLoading();
			$.messager.alert('Publish Category Failed',json2String(data),'error');
		}
  });		
}