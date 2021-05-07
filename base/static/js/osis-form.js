const DEFAULT_CONFIGURATION = {
    errorClass: "has-error",
    successClass: "",
    trigger: "focusin focusout",
    classHandler: function (inputField) {
        return $(inputField.element.closest(".form-group") || inputField.element.closest("div"));
    },
    errorsContainer: function (inputField) {
        return inputField.$element.closest(".form-group")
    },
    errorsWrapper: '<div class="help-block"></div>',
    errorTemplate: '<p></p>',
    excluded: 'input[type=button], input[type=submit], input[type=reset], input[type=hidden], [disabled]',
}

$(document).ready(function () {
    init();
})

document.addEventListener("formAjaxSubmit:error", function (e) {
    init();
})

$('#form-ajax-modal').on("shown.bs.modal", function (e) {
    init();
})

function init() {
    styleBusinessErrorMessages();
    window.Parsley.addAsyncValidator('async-osis', remoteFieldValidation);

    $(".osis-form").parsley(DEFAULT_CONFIGURATION);

    // In case of invalid input for type integer, the value accessible from js is "", therefore you would never got an error.
    $(".osis-form").each(function () {
        $(this).parsley().validate({group: "validateOnLoad", force: true});
        addValidationOnNumberInput($(this));
        enableValidationEmptyOnSemiRequiredField($(this));
    })


    window.Parsley.on('field:success', function () {
        const inputField = this;
        if (inputField.warning !== undefined && inputField.warning !== null) {
            displayWarning(inputField);
        } else {
            hideWarning(inputField)
        }

        if (inputField.element.hasAttribute("semi-required")) {
            if (inputField.element.value === "") {
                inputField._ui.$errorClassHandler.addClass("has-warning");
            }
        }
    })

    window.Parsley.on('form:error', function () {
        highlightFormTabsWithError()
    })
    highlightFormTabsWithError()
}

function styleBusinessErrorMessages() {
    const messagesContainers = document.querySelectorAll(".osis-form div[class=help-block]");
    for (let container of messagesContainers) {
        container.classList.add("has-error");
    }
}

function displayWarning(inputField) {
    inputField._ui.$errorClassHandler.removeClass("has-success");
    inputField._ui.$errorClassHandler.addClass("has-warning");
    inputField._ui.$errorsWrapper.text(inputField.warning);
    inputField._insertErrorWrapper();
}

function hideWarning(inputField) {
    if(inputField._ui !== undefined && inputField._ui.$errorClassHandler.hasClass("has-warning")){
        inputField._ui.$errorClassHandler.removeClass("has-warning");
        inputField._ui.$errorsWrapper.text("");
    }
}

function remoteFieldValidation(xhr) {
    const inputField = this;
    return xhr.then(function (jsonResponse) {
        if (!jsonResponse["valid"]) {
            hideWarning(inputField);
            return $.Deferred().reject(jsonResponse["msg"]);
        }
        inputField.warning = jsonResponse["msg"];
        return true;
    })
}

function addValidationOnNumberInput($form) {
    $form.find("input[type=number]").each(function () {
        convertNumberInputToTextInputWithNumberValidation($(this));
    })
}

function enableValidationEmptyOnSemiRequiredField($form) {
    $form.find("[semi-required]").each(function () {
        $(this).attr("data-parsley-validate-if-empty", "")
    })
}

function convertNumberInputToTextInputWithNumberValidation($numberInput) {
    const isDecimal = isDecimalInput($numberInput);

    $numberInput.attr("type", "text");
    $numberInput.attr("data-parsley-type", isDecimal ? "number" : "integer");
}

function isDecimalInput($numberInput) {
    return $numberInput.attr("step") !== undefined;
}

function highlightFormTabsWithError() {
    const formTabsUl = document.getElementsByClassName("form-tab");
    for (const tabUlElement of formTabsUl) {
        const tabContentElement = getTabContentElementFromTabUl(tabUlElement);
        if (doesTabContainsErrors(tabContentElement)) {
            highlightTabUl(tabUlElement)
        }
    }
}

function getTabContentElementFromTabUl(tabUlElement) {
    const anchorElement = tabUlElement.getElementsByTagName("A")[0]
    const tabContentId = anchorElement.getAttribute("href").replace("#", "")
    return document.getElementById(tabContentId)
}

function doesTabContainsErrors(tabContentElement) {
    return tabContentElement.getElementsByClassName('has-error').length > 0 || tabContentElement.getElementsByClassName('has-warning').length > 0
}

function highlightTabUl(tabUlElement) {
    tabUlElement.classList.add("contains-error");
    displayFormDangerMessage(gettext('Error(s) in form: The modifications are not saved'));
}


function displayFormDangerMessage(message) {
    const panelErrorMessages = document.querySelector("#pnl_error_messages");
    const panelListItems = panelErrorMessages.querySelectorAll("ul > li");
    const currentMessages = Array.from(panelListItems).map(e => e.textContent.trim());
    if (!currentMessages.includes(message)) {
        panelErrorMessages.classList.remove("hidden");
        const newItem = document.createElement("li");
        newItem.innerText = message
        panelErrorMessages.querySelector("ul").append(newItem);
    }
}