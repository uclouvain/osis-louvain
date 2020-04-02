const trans_existing_version_name = gettext('Existing name version');
const trans_invalid_version_name = gettext('Invalid name version');

function validate_version_name() {
    cleanErrorMessage();
    let newVersionName = extractValue($('#id_acronym'));
    let validationUrl = $('#SpecificVersionForm').data('validate-url');
    validateVersionNameAjax(validationUrl, newVersionName, callbackVersionNameValidation);
}


function callbackVersionNameValidation(data) {
    if (data['existing']) {
        setErrorMessage(trans_existing_version_name, '#acronym_error_id');
    }else if (!data['valid']) {
        setErrorMessage(trans_invalid_version_name, '#acronym_error_id');
    }
}

function validateVersionNameAjax(url, acronym, callback) {
    /**
     * This function will check if the acronym exist or have already existed
     **/
    queryString = "?acronym=" + acronym;
    $.ajax({
        url: url + queryString
    }).done(function (data) {
        callback(data);
    });
}

function extractValue(domElem) {
    return (domElem && domElem.val()) ? domElem.val() : "";
}

function setErrorMessage(text, element) {
    parent = $(element).closest(".acronym-group");
    if (parent.find('.help-block').length === 0) {
        parent.addClass('has-error');
        parent.append("<div class='help-block'>" + text + "</div>");
    }
}

function cleanErrorMessage() {
    parent = $("#id_acronym").closest(".acronym-group");
    parent.removeClass('has-error');
    parent.removeClass('has-warning');
    parent.find(".help-block").remove();
    parent.find(".has-error").removeClass('has-error');
}

$(document).ready(function () {
    $(function () {
        $('#id_acronym').change(validate_version_name);
    });
});
