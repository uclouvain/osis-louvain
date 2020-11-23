const DEFAULT_CONFIGURATION = {
    errorClass: "has-error",
    successClass: "has-success",
    trigger: "focusin focusout",
    classHandler: function (inputField){
        return inputField.$element.closest("div");

    },
    errorsWrapper: '<div class="help-block"></div>',
    errorTemplate: '<p></p>',
}

$(document).ready(function () {
    $(".osis-form").parsley(DEFAULT_CONFIGURATION);

    // In case of invalid input for type integer, the value accessible from js is "",
    // therefore you would never got an error.
    $(".osis-form").each(function(){
        addValidationOnNumberInput($(this));
    })

    window.Parsley.on('form:error', function (){
        highlightFormTabsWithError()
    })

    highlightFormTabsWithError()
})

function addValidationOnNumberInput($form){
    $form.find("input[type=number]").each(function(){
        convertNumberInputToTextInputWithNumberValidation($(this));
    })
}

function convertNumberInputToTextInputWithNumberValidation($numberInput){
    const isDecimal = isDecimalInput($numberInput);

    $numberInput.attr("type", "text");
    $numberInput.attr("data-parsley-type", isDecimal ? "number" : "integer");
}

function isDecimalInput($numberInput){
    return $numberInput.attr("step") !== undefined;
}

function highlightFormTabsWithError(){
    const formTabsUl = document.getElementsByClassName("form-tab");
    for (const tabUlElement of formTabsUl){
        const tabContentElement = getTabContentElementFromTabUl(tabUlElement);
        if (doesTabContainsErrors(tabContentElement)) {
            highlightTabUl(tabUlElement)
        }
    }
}

function getTabContentElementFromTabUl(tabUlElement){
    const anchorElement = tabUlElement.getElementsByTagName("A")[0]
    const tabContentId = anchorElement.getAttribute("href").replace("#", "")
    return document.getElementById(tabContentId)
}

function doesTabContainsErrors(tabContentElement){
    return tabContentElement.getElementsByClassName('has-error').length > 0 || tabContentElement.getElementsByClassName('has-warning').length > 0
}

function highlightTabUl(tabUlElement){
    tabUlElement.classList.add("contains-error");
}