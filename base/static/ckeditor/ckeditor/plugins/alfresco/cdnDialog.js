var alfresco_parent_id;
var alfresco_document_id;
var alfresco_document_name;
var alfresco_document_title;

	CKEDITOR.dialog.add( 'alfrescoDialog', function( editor ) {

		// define a dialog box with 2 tabs: "Browse" and "Upload"
		// and tell what to do when "ok" button clicked

	  return {

		title : 'Insertion d\'un lien vers un document Alfresco',
		resizable : CKEDITOR.DIALOG_RESIZE_HEIGHT,
		minWidth : 600,
		minHeight : 480,
		contents : [
		  {
			id : "alfresco_browse",
			label : 'Sélection du fichier cible',
			title : 'tab1: Browse',
			expand : true,
			elements :[
			  {
				id : "iframe_alfresco_browse",
				src : alfrescoBrowseTabPath,
				type : 'iframe',
				label : 'Link to Alfresco Doc',
				width : '100%',
				height : 480
			  }
			]
		  },
		  {
			id : "alfresco_upload",
			label : 'Dépôt dans alfresco + sélection',
			title : 'tab2: Upload',
			expand : true,
			elements :[
			  {
				id : "iframe_alfresco_upload",
				src : alfrescoUploadTabPath,
				type : 'iframe',
				label : 'Upload doc to Alfresco',
				width : 1000,
				height : 480
			  }
			]
		  }
		],
		onOk: function() {

		  if ( alfresco_document_id == null ) {
			alert("Vous devez faire une sélection avant de cliquer 'ok'");
			return false;
		  }

		  var sel = editor.getSelection();
		  var selectedText = sel.getSelectedText( ) ;
		  var link = editor.document.createElement( 'a' );

		  var href = alfrescoDownloadPath.replace("alfresco_document_id", alfresco_document_id);
		  href = href.replace("alfresco_document_name", alfresco_document_name);

		  // user has selected/highlighted some text in the editor window
		  if (selectedText!=null && selectedText.length != 0) {
			 link.setHtml(selectedText);
		  }
		  else {
			// no selection, we have to create the html text of the link with either the title or the the name of the file
			if ( alfresco_document_title!=null && alfresco_document_title.length != 0) link.setHtml(" "+alfresco_document_title+" ");
			else link.setHtml(" "+alfresco_document_name+" ");
		  }

		  link.setAttribute( 'href', href);
		  link.setAttribute('target', '_blank');
		  if ( alfresco_document_title!=null ) link.setAttribute( 'title', alfresco_document_title);
		  editor.insertElement( link );

		}
	  }

	});



//
// automatic dialog re size  feature
//
	CKEDITOR.dialog.on('resize', function (evt) {
	  var dialog = CKEDITOR.dialog.getCurrent();
	  if ( dialog ) {
		dialog = dialog._.contents;
		var BrowseIframeId = dialog.alfresco_browse.iframe_alfresco_browse._.frameId;
		var UploadIframeId = dialog.alfresco_upload.iframe_alfresco_upload._.frameId;
		var instanceBrowse = document.getElementById(BrowseIframeId);
		var instanceUpload = document.getElementById(UploadIframeId);
		instanceBrowse.style.height = evt.data.height + 'px';
		instanceUpload.style.height = evt.data.height + 'px';
	  }
	});



