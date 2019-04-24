// define a listener to receive message with dats from iframe

	function alfrescoCallback(e) {

		if(e.origin === "https://uclouvain.be/PPE-filemanager/") {

			  obj = JSON.parse(e.data);
			  alfresco_document_id = obj.doc_id;
			  alfresco_parent_id = obj.parent_id;
			  alfresco_document_name = decodeURIComponent(obj.doc_name);
			  alfresco_document_title = decodeURIComponent(obj.doc_title);

		}
	}

	window.addEventListener("message", alfrescoCallback, false);


