let linkButtonNoSpinnerClicked = false;

function bindNoSpinner(elem){
    linkButtonNoSpinnerClicked = elem ? elem.hasClass("no_spinner") : false;
}

function closeOverlaySpinner(){
    $("#loader").hide();
    document.getElementById("overlay").style.display = "none";
    document.getElementById("overlay_fadein").style.display = "none";
}

$( document ).ready(function() {
    closeOverlaySpinner();
    $('a, button').on('click submit', function (e) {
        bindNoSpinner($(this));
    });

    ["formAjaxSubmit:onSubmit", "prepareXls:onClick"].forEach( evt =>
        document.addEventListener(evt, function (e) {
            bindNoSpinner(e.detail);
        })
    );
});

$( document ).on( 'keyup', function ( e ) {
    if ( e.key === 'Escape' ) { // ESC
        closeOverlaySpinner();
    }
});

window.addEventListener('beforeunload', function (e) {
    if (! linkButtonNoSpinnerClicked) {
        $("#loader").show();
        document.getElementById("overlay_fadein").style.display = "block";
    }
});
