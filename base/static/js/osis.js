$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
    check_browser();
    collapseWarnings();
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
    if (keycode_is_enter(e)) {
        e.preventDefault();
    }
    return false;
}


function select_next_input_value(e){
    var target = e.data.target;
    if (keycode_is_enter(e)) {
        window.scrollBy(0, this.scrollHeight + 19);
        var index = $(target).index(this);
        if (this.tabIndex >= e.data.table_size){
            $(target).eq(index).blur();
        }
        else{
            $(target).eq(index + e.data.index_increment_value).select().focus();
        }
        disable_enter(e);
    }
    else if (keycode_is_tab(e)) {
        window.scrollBy(0, this.scrollHeight + 19);
    }
}


function keycode_is_enter(event){
    var keyCode = event.keyCode || event.which;
    return keyCode === 13;
}

function keycode_is_tab(event){
    var keyCode = event.keyCode || event.which;
    return keyCode === 9;
}

function originalValueChanged(values, id, score, justification) {
    if (score == null || score == "") {
        score = -1;
    } else {
        score = parseFloat(score);
    }

    if (justification == null) justification = '';

    for (i = 0; i < values.length; i++) {
        if (values[i][0] == id) {
            if(score == parseFloat(values[i][1].replace(",", ".")) && justification == values[i][2]) {
                return false;
            } else {
                return true;
            }
        }
    }
    return null;
}

function check_browser(){
    var browser = get_browser();
    var accepted = false;
    if (browser.name in browser_supported_versions){
        var accepted_version = browser_supported_versions[browser.name];
        if (browser.version >= accepted_version) {
            accepted = true;
        }
    }
    if(accepted) {
        $("#alert_wrong_version").hide();
    } else {
        $("#alert_wrong_version").show();
    }
}

function get_browser() {
    var ua=navigator.userAgent,tem,M=ua.match(/(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i) || [];
    if(/trident/i.test(M[1])){
        tem=/\brv[ :]+(\d+)/g.exec(ua) || [];
        return {name:'ie',version:(tem[1]||'')};
    }
    if(M[1]==='Chrome'){
        tem=ua.match(/\bOPR\/(\d+)/);
        if(tem!=null)   {return {name:'opera', version:tem[1]};}
    }
    M=M[2]? [M[1], M[2]]: [navigator.appName, navigator.appVersion, '-?'];
    if((tem=ua.match(/version\/(\d+)/i))!=null) {M.splice(1,1,tem[1]);}
    return {
        name: M[0].toLowerCase(),
        version: M[1].toLowerCase()
    };
}

var browser_supported_versions = {
    firefox: 46,
    chrome: 50,
    opera: 37,
    ie: 10,
    safari: 8,
    edge: 24
};

function setEventKeepIds(domTableId, localStorageKey) {
    if(typeof localStorage!=undefined) {
        if (domTableId == undefined || localStorageKey == undefined){ return;}

        var table = $('#' + domTableId)
        if (table != undefined) {
            table.on('init.dt order.dt', function() {
                var orderList = [];
                table.find('tr').each(function() {
                    var id = $(this).attr('data-id');
                    var value = $(this).attr('data-value');
                    if (id != undefined) {
                         orderList.push({'id': id, 'value': value});
                    }
                });
                if(orderList.length > 0){
                    localStorage.setItem(localStorageKey, JSON.stringify(orderList));
                }
            });
        }
    }
}

function displayInfoMessage(jsonResponse, containerId) {
    var message_info_container = document.getElementById(containerId);
    message_info_container.innerHTML = jsonResponse['success_message'];
    message_info_container.style.display = "block";
    message_info_container.style.visibility = "visible";
}

function collapseWarnings() {
    let collapse_warnings = $('#CollapseWarnings');
    let expand_button = $('#btn_expandButton');
    //To open by default collapse of warnings
    collapse_warnings.collapse('toggle');

    collapse_warnings.on("hide.bs.collapse", function(){
        expand_button.html('<span id="expandButton" class="glyphicon glyphicon-collapse-down" style="color:#8a6d3b"></span>');
        expand_button.attr("title", gettext("Open"));
    });

    collapse_warnings.on("show.bs.collapse", function(){
        expand_button.html('<span id="expandButton"  class="glyphicon glyphicon-collapse-up" style="color:#8a6d3b"></span>');
        expand_button.attr("title", gettext("Collapse"));
    });
}