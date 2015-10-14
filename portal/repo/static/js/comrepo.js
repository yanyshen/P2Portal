

function loadCompositeInfo(){
	$.ajax({     
		type: "GET",  
		url:  "/composite/"+treeNode.id+"/",  
		cache: false,  
		async:true,  
		dataType :'json',
		data:"",
		success:function(data){ 
		 var sourceJson =data;
		 $('#show-comName').val(sourceJson.name);
		 $('#show-compoUpdateSite').attr("href",sourceJson.update_site_url);
		 $('#show-compoUpdateSite').html(sourceJson.update_site_url);
		 repos = sourceJson.repositories;
		 var rows  = $("#show-repos").datagrid('getRows') ;
		 if(rows.length == repos.length){
		    $("#show-repos").datagrid('checkAll');
		 }
		 for(var i=0; i<repos.length;i++){
			 var repoId = repos[i];
			 var rowIndex = $("#show-repos").datagrid('getRowIndex', repoId);
			 $("#show-repos").datagrid('checkRow', rowIndex);
			 $("#show-repos").datagrid('selectRecord', repoId);
		 }
	   }
	 });		
}

function saveCompositeInfo(){
	var name =$('#show-comName').val();
	if(!name){
		$.messager.alert('Composite','The name is required!','error');
		return;
	}	
	var pattern = /^\w+$/;
	if(!pattern.test(name)){
	   $.messager.alert('Illegal name','The name should be number, char or underscore, please input it again!','error');
	   return;
	}				
	var rows = $('#show-repos').datagrid('getSelections');
	if(!rows || rows.length == 0){
//		$("#alertInfo").html('No repository is referred by this composite.');
//		$("#alertInfo").show();
	}
    var dataValues="";
	for(var i=0;i<rows.length;i++){
	     dataValues +="repositories="+rows[i].id;
		if(i !=rows.length -1){
		  dataValues +="&";
		}
	}	
    showLoading();				
	$.ajax({     
		type: "POST",  
		url:  "/composite/"+treeNode.id+"/",
		cache: false,  
		async:true,  
		dataType :'*',
		data:"name="+ name+"&"+dataValues,
		success:function(data){  
			hideLoading();
			$.messager.alert('Success', 'Save successfully.', "info");
//			$.messager.show({
//				title:'Success',
//				msg:'Save successfully.',
//				timeout:4000,
//				showType:'slide'
//			});
	   },
		error:function(data,status,e){
			hideLoading();
			if(e=='FORBIDDEN'){
				$.messager.alert('Save Failed',"You don\'t have such permisson.",'error');
		         }else {
		    	$.messager.alert('Save Failed',' Failed','error');
		       }
			}
		

		
  });
}

function deleteComposite(){
	$.ajax({     
		type: "DELETE",  
		url:  "/composite/"+treeNode.id+"/",  
		cache: false,  
		async:false,  
		dataType :'*',
		data:"",
		success:function(data){ 
			parent.loadDataForTree();
			parent.goHome();
			$.messager.show({
				title:'Success',
				msg:'Delete composite repository successfully',
				timeout:4000,
				showType:'slide'
			});
	   } ,
		error:function(data,status,e){
			if(e=='FORBIDDEN'){
				$.messager.alert('Delete Failed',"You don\'t have such permisson.",'error');
		         }else {
		    	$.messager.alert('Delete Failed',' Failed','error');
		       }
			
			
		}
	 }); 
}
