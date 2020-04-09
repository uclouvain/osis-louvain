const trans_existing_version_name = gettext('Existing name version');
const trans_existed_version_name = gettext('Existed name version');
const trans_invalid_version_name = gettext('Invalid name version');

function validate_version_name() {
    cleanErrorMessage();
    let newVersionName = extractValue($('#id_version_name'));
    let validationUrl = $('#SpecificVersionForm').data('validate-url');
    validateVersionNameAjax(validationUrl, newVersionName, callbackVersionNameValidation);
}


function callbackVersionNameValidation(data) {
    cleanErrorMessage();
    if (data['existing_version_name']) {
        setErrorMessage(trans_existing_version_name, '#version_name_error_id');
    }else if (data['existed_version_name']) {
        setWarningMessage(trans_existed_version_name, '#version_name_error_id');
    }else if (!data['valid']) {
        setErrorMessage(trans_invalid_version_name, '#version_name_error_id');
    }
}

function validateVersionNameAjax(url, version_name, callback) {
    /**
     * This function will check if the acronym exist or have already existed
     **/
    queryString = "?version_name=" + version_name;
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
    parent = $(element).closest(".version_name-group");
    if (parent.find('.help-block').length === 0) {
        parent.addClass('has-error');
        parent.append("<div class='help-block'>" + text + "</div>");
    }
}

function setWarningMessage(text, element){
    parent = $(element).closest(".version_name-group");
    parent.addClass('has-warning');
    parent.append("<div class='help-block'>" + text + "</div>");
}

function cleanErrorMessage() {
    parent = $("#id_version_name").closest(".version_name-group");
    parent.removeClass('has-error');
    parent.removeClass('has-warning');
    parent.find(".help-block").remove();
    parent.find(".has-error").removeClass('has-error');
}

$(document).ready(function () {
    $(function () {
        $('#id_version_name').change(validate_version_name);
    });
});
