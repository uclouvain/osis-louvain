	(
	  function() {

		CKEDITOR.plugins.add( 'cdn', {

		  requires : [ 'iframedialog' ],
		  init: function( editor ) {
			editor.addCommand( 'cdnDialog', new CKEDITOR.dialogCommand( 'cdnDialog', { } ) );
			editor.ui.addButton( 'CDN', {
			  label: 'Lien vers document du CDN',
			  command: 'cdnDialog',
			  icon: 'cdn.png'
			});
			CKEDITOR.dialog.add( 'cdnDialog', this.path + 'cdnDialog.js' );
			CKEDITOR.scriptLoader.load(this.path + 'cdnCallback.js' );
		  }
		});

	  }

	)();