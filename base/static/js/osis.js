$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});

$("#bt_remove").click(function(event) {
    return confirm("Oui?");
});

$.ajaxSetup({
     beforeSend: function(xhr, settings) {
         function getCookie(name) {
             var cookieValue = null;
             if (document.cookie && document.cookie != '') {
                 var cookies = document.cookie.split(';');
                 for (var i = 0; i < cookies.length; i++) {
                     var cookie = jQuery.trim(cookies[i]);
                     // Does this cookie string begin with the name we want?
                     if (cookie.substring(0, name.length + 1) == (name + '=')) {
                         cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                         break;
                     }
                 }
             }
             return cookieValue;
         }
         if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
             // Only send the token to relative URLs i.e. locally.
             xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
         }
     }
});

function invalidScoreMsg(input,decimal_allowed,message_decimal,message_max_score){
    if (input.value > 20){
        input.setCustomValidity(message_max_score)
    }
    else if (input.value != Math.floor(input.value) && !decimal_allowed){
        input.setCustomValidity(message_decimal)
    }
    else{
         input.setCustomValidity('');
    }
}

function disable_enter(e) {
    var keyCode = e.keyCode || e.which;
    if (keyCode === 13) {
        e.preventDefault();
    }
    return false;
}