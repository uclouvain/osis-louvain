function addOnClickEventOnPrepareXls(e) {
    document.dispatchEvent(new CustomEvent("prepareXls:onClick", {
        "detail": $(e.target)
    }));
}

function prepare_xls(e, action_value){
    e.preventDefault();
    addOnClickEventOnPrepareXls(e);
    let status = $("#xls_status");
    status.val(action_value);
    $("#search_form").submit();
    status.val('');
}
