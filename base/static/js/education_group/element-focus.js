document.addEventListener("DOMContentLoaded", function(event) {
    var eltidfocus = localStorage.getItem('eltidfocus');
    if (eltidfocus){
        var elt = document.getElementById(eltidfocus);
        if (elt){
            elt.focus();
            elt.scrollIntoView({'block': 'center', 'inline': 'center'});
        }
    }
});

$('.btn_to_focus').click(function (evt) {
    localStorage.setItem('eltidfocus', this.id);
});
