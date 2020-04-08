let linkButtonNoSpinnerClicked = false;

//sync spinner is always active on page load
const spinnerActive = {sync: true, async: false};

function bindNoSpinner(elem){
    linkButtonNoSpinnerClicked = elem ? elem.hasClass('no_spinner') : false;
}

function showOverlaySpinner(async= false) {
    $('#loader, #overlay-fade-in').show();
    spinnerActive[async ? 'async' : 'sync'] = true;
}

function closeOverlaySpinner(async= false){
    // hide according to initial trigger
    if(spinnerActive[async ? 'async' : 'sync'] && !spinnerActive[!async ? 'async' : 'sync']) {
        $('#loader, #overlay, #overlay-fade-in').hide();
        spinnerActive[async ? 'async' : 'sync'] = false;
    }
}

$(document).ready(function() {
    closeOverlaySpinner();
    $('a, button').on('click submit', function (e) {
        bindNoSpinner($(this));
    });

    ["formAjaxSubmit:onSubmit", "prepareXls:onClick"].forEach(evt =>
        document.addEventListener(evt, function (e) {
            bindNoSpinner(e.detail);
        })
    );
});

$(document).on('keyup', function (e) {
    if ( e.key === 'Escape' ) { // ESC
        closeOverlaySpinner();
    }
});

window.addEventListener('beforeunload', function (e) {
    if (! linkButtonNoSpinnerClicked) {
        showOverlaySpinner();
    }
});

$(document).ajaxStart(function(){
    showOverlaySpinner(true);
}).ajaxStop(function(){
    closeOverlaySpinner(true);
});
