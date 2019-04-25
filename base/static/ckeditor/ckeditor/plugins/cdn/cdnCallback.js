// define a listener to receive message with dats from iframe

	function cdnCallback(e) {
		if(e.origin === "https://uclouvain.be") {
			  obj = e.data;
			  cdn_document_url = obj.documentURL;
			  cdn_document_name = decodeURIComponent(obj.documentName);
		}
	}

	window.addEventListener("message", cdnCallback, false);


