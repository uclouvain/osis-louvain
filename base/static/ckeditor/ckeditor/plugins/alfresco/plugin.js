	(
	  function() {

		CKEDITOR.plugins.add( 'alfresco', {

		  requires : [ 'iframedialog' ],
		  init: function( editor ) {
			editor.addCommand( 'alfrescoDialog', new CKEDITOR.dialogCommand( 'alfrescoDialog', { } ) );
			editor.ui.addButton( 'Alfresco', {
			  label: 'Lien vers document Alfresco',
			  command: 'alfrescoDialog',
			  icon: 'alfresco.png'
			});
			CKEDITOR.dialog.add( 'alfrescoDialog', this.path + 'cdnDialog.js' );
			CKEDITOR.scriptLoader.load(this.path + 'cdnCallback.js' );
		  }
		});

	  }

	)();