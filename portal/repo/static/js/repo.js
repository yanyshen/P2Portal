//repo.js
function loadHistory(){
	$.ajax({     
		type: "GET",  
		url:  "/repository/"+treeNode.id+"/operations/?limit=20",  
		cache: false,  
		async:false,  
		dataType :'json',
		data:"",
		success:function(data){ 
			var jsonData =buildOperationJson(data, 20);
			$('#history').datagrid('loadData',jsonData);
			if(jsonData && jsonData.length <=1){
			  $('#rollbackBtn').css("display","none");
			  $('#cleanupBtn').css("display", "none");
			}else{
			  $('#rollbackBtn').css("display","");
			  $('#cleanupBtn').css("display","");
			}
	   },
	    error:function(data){
		  $.messager.alert('Failed', 'Load History failed!', 'error');
		}
	 });
}
function loadRepoInfo(){
		// ajax get call to load current repository information
	   // If the tree ndoe is not repository,a error will occur. In this case, error is omitted.
	var prefix=	'';
	//$.getJSON('portal.conf',function(data1){
	 
		$.ajax({     
			type: "GET",  
			url:  "/repository/"+treeNode.id+"/",  
			cache: false,  
			async:false,  
			dataType :'json',
			data:"",
			success:function(data){
				var sourceJson =data;
				$('#show-repoName').val(sourceJson.name);
				$('#show-siteUrl').attr("href",filterURL(sourceJson.update_site_url));
			   // $('#show-siteUrl').attr("href",data1.SITE_URL_ROOT+filterURL(sourceJson.update_site_url));
				$('#show-siteUrl').html(sourceJson.update_site_url);
			    $('#show-repoDescription').val(sourceJson.description);
		   } 
		 });
	//}) 
	
	
}

function doPublish(){
	var archive = $('#archive').val();

	if (!archive) {
		$.messager.alert('Archive', 'The archive is required!', 'error');
		return;
	}
	var comment = $('#p-comment').val();
	if (!comment) {
		$.messager.alert('Comment', 'The comment is required!', 'error');
		return;
	}
	$("#publishDlg").modal("hide");
	comment = handleSpecialChar(comment);
	showLoading();
	var postData = '{"comment":"' + comment + '"}';
	
	var jsonPostData = eval("(" + postData + ")");
	// upload file
	$.ajaxFileUpload({
		url : '/repository/' + treeNode.id + '/publish/',
		secureuri : false,
		fileElementId : 'archive',
		dataType : '*',
		data : jsonPostData,
		success : function(data, status) {
			loadHistory();
			hideLoading();
			if(data=='Forbidden'){
			$.messager.alert('Publish Failed',
						"You don\'t have such permisson.", 'error');
			}else{
				$.messager.show({
					title:'Success',
					msg:'Publish successfully.',
					timeout:4000,
					showType:'slide'
				});
			}
		},
		error : function(data, status, e) {
			hideLoading();
			$.messager.alert('Publish Failed',
					"please check your publish package", 'error');

		}

	});
}
function doMirror(){
	var mirrorURL =$('#mirrorUrl').combobox('getValue');
	if(!mirrorURL){
		$.messager.alert('Mirror','The mirror URL is required!','error');
		return;
	}
	
	var comment =$('#m-comment').val();
	if(!comment){
		$.messager.alert('Mirror','The comment is required!','error');
			return;
	}
	$("#mirrorDlg").modal("hide");
    mirrorURL = escape(handleSpecialChar(mirrorURL).Trim());
	comment =  handleSpecialChar(comment);
	showLoading();
	// mirror 
	$.ajax({     
		type: "POST",  
		url:  "/repository/"+treeNode.id+"/mirror/",
		cache: false,  
		async:false,  
		dataType :'*',
		data:"mirror_url=" +mirrorURL+"&comment="+comment,
		success:function(data){  
			loadHistory();
			hideLoading();
			$.messager.show({
				title:'Success',
				msg:'Mirror successfully.',
				timeout:4000,
				showType:'slide'
			});
	   },
		error:function(data,status,e){
			hideLoading();
			if(e=='FORBIDDEN'){
				$.messager.alert('Mirror Failed',"You don\'t have such permisson.",'error');
		         }else {
		    	$.messager.alert('Mirror Failed','Mirror Failed','error');
		       }
			
		}
  });
}
//edit and save
function doSave(){
	var name =$("#e-repoName").val();
	var description =$("#e-repoDescription").val();
	if(!name){
            $.messager.alert('Mirror','The name is required!','error');
	    return;
	}
	var pattern = /^\w+$/;
	if(!pattern.test(name)){
	   $.messager.alert('Illegal name','The name should be number, char or underscore, please input it again!','error');
	   return;
	}
	if(!description){
	   $.messager.alert('Mirror','The description is required!','error');
		return;
    }
 
	name =handleSpecialChar(name);
	description = handleSpecialChar(description);
	showLoading();
	// save repository
	$.ajax({		
		type: "POST",  
		url:  "/repository/"+treeNode.id+"/",
		cache: false,  
		async: false,  
		dataType :'*',
		data:"name="+name+"&description=" +description,
		success:function(data){  
			hideLoading();
			$("#show-repoName").val($("#e-repoName").val());
			$("#show-repoDescription").val($("#e-repoDescription").val());
			$("#editDlg").modal('hide'); //after hide e-reponame, e-repoDescription will be set null
			
			$.messager.show({
				title:'Success',
				msg:'Modify repository information successfully',
				timeout:4000,
				showType:'slide'
			});
	   },
		error:function(data,status,e){
			hideLoading();
			if(e=='FORBIDDEN'){
				$.messager.alert('Edit Failed',"You don\'t have such permisson.",'error');
		         }else {
		    	$.messager.alert('Edit Failed',' Failed','error');
		       }
			}
		
  });
}
function doDelete(){
	//delete the repo from db and file system
	showLoading();
	$.ajax({     
		type: "DELETE",  
		url:  "/repository/"+treeNode.id+"/",  
		cache: false,  
		async:false,  
		dataType :'*',
		data:"",
		success:function(data){ 
			hideLoading();
			parent.loadDataForTree();
			parent.goHome();
			$.messager.show({
				title:'Success',
				msg:'Delete repository successfully',
				timeout:4000,
				showType:'slide'
			});
	   } ,
		error:function(data,status,e){
			hideLoading();
			if(e=='FORBIDDEN'){
				$.messager.alert('Delete Failed',"You don\'t have such permisson.",'error');
		         }else {
		    	$.messager.alert('Delete Failed',' Failed','error');
		       }
		}
	 }); 
}
function doCleanup(){
	showLoading();
	$.ajax({     
		type: "POST",  
		url: "/repository/"+treeNode.id+"/cleanup/",  
		cache: false,  
		async:true,  
		dataType :'*',
		data:"",
		success:function(data){  
			hideLoading();
			loadHistory();
			$.messager.show({
				title:'Success',
				msg:'Cleanup repository successfully',
				timeout:4000,
				showType:'slide'
			});
	   },
		error:function(data,status,e){
			hideLoading();
			if(e=='FORBIDDEN'){
				$.messager.alert('Clean Up Failed',"You don\'t have such permisson.",'error');
		         }else {
		    	$.messager.alert('Clean Up Failed',' Failed','error');
		       }
			
		}
  });
}
function doRollback(){
	showLoading();
	$.ajax({     
		type: "POST",  
		url: "/repository/"+treeNode.id+"/rollback/",  
		cache: false,  
		async:true,  
		dataType :'*',
		data:"",
		success:function(data){  
			hideLoading();
			loadHistory();
			$.messager.show({
				title:'Success',
				msg:'Rollback successfully',
				timeout:4000,
				showType:'slide'
			});
	   },
		error:function(data,status,e){
			hideLoading();
			if(e=='FORBIDDEN'){
				$.messager.alert('Rollback Failed',"You don\'t have such permisson.",'error');
		         }else {
		    	$.messager.alert('Rollback Failed',' Failed','error');
		       }
			}
  });
}

function showDetailedInfo(rowIndex,rowData){
	$("#detailedPane").show();
	if(rowData.type == "P" || rowData.type =="M" || rowData.type=="S" || rowData.type == "C"){
		   $.ajax({     
			type: "GET",  
			url:  "/operation/"+rowData.id+"/",  
			cache: false,  
			async:false,  
			dataType :'json',
			data:"",
			success:function(data){ 
                var sourceJson = data;
                var output ="";
                for(var key in sourceJson){
					if(key == "A"){
						if(sourceJson[key] && sourceJson[key].length>0){
						  output += "<h4>Added:</h4>"+formatOutputString(sourceJson[key])+"<BR>";
						}
					}else if(key =="M"){
						if(sourceJson[key] && sourceJson[key].length>0){
							output += "<h4>Modified:</h4>"+formatOutputString(sourceJson[key])+"<BR>";
						}
					}else if(key =="D"){
						if(sourceJson[key] && sourceJson[key].length>0){
							output += "<h4>Deleted:</h4>"+formatOutputString(sourceJson[key])+"<BR>";
						}
					}
				}
				$('#detailedContent').html(output);
		   } 
		 });  

	 }else{
	     $('#detailedContent').html('No Operation Detailed Message');
	 }
}

