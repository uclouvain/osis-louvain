const internship = "INTERNSHIP";
const LEARNING_UNIT_FULL_SUBTYPE = "FULL";
const trans_existed_acronym = gettext('existed_acronym');
const trans_existing_acronym = gettext('existing_acronym');
const trans_invalid_acronym = gettext('invalid_acronym');
const trans_field_required = gettext('field_is_required');
const trans_field_min = gettext('min_for_field');
const trans_field_max = gettext('max_for_field');

var form = $('#LearningUnitYearForm').closest("form");
var InitialAcronym;


function isLearningUnitSubtypeFull(){
   return learning_unit_current_subtype === LEARNING_UNIT_FULL_SUBTYPE;
}


function isValueEmpty(html_id){
    return document.getElementById(html_id).value === ""
}


function isDisabledField(html_id){
    return document.getElementById(html_id).disabled === true
}


function showInternshipSubtype(){
    if (isLearningUnitSubtypeFull() && document.getElementById('id_internship_subtype')) {
        var container_type_value = document.getElementById('id_container_type').value;
        var value_not_internship = container_type_value !== internship;
        var labelElem = $("label[for='id_internship_subtype']");

        document.getElementById('id_internship_subtype').disabled = value_not_internship;
        if (value_not_internship) {
            $('#id_internship_subtype')[0].selectedIndex = 0;
            $('#lbl_internship_subtype_error').empty(); // Remove error message if exist
            labelElem.text(labelElem.text().replace('*','')) // Remove asterix in order to indicate field not required
        }
    }
}

function updateAdditionalEntityEditability(elem, id, disable_only){
    var empty_element = elem === "";
    if (empty_element){
        $('#'.concat(id))[0].selectedIndex = 0;
        document.getElementById(id).disabled = true;
    }
    else if (!disable_only){
        document.getElementById(id).disabled = false;
    }
}

function validate_acronym() {
    cleanErrorMessage();
    var newAcronym = getCompleteAcronym();
    if (newAcronym !== InitialAcronym) {
        var validationUrl = $('#LearningUnitYearForm').data('validate-url');
        var year_id = $('#id_academic_year').val();
        validateAcronymAjax(validationUrl, newAcronym, year_id, callbackAcronymValidation);
    }
}


function cleanErrorMessage(){
    parent = $("#id_acronym_0").closest(".acronym-group");
    parent.removeClass('has-error');
    parent.removeClass('has-warning');
    parent.children(".help-block").remove();
}


function getCompleteAcronym(){
    var acronym = getFirstLetter() + getAcronym() + getPartimCharacter();
    return acronym.toUpperCase();
}

function extractValue(domElem){
    return (domElem && domElem.val()) ? domElem.val(): "";
}


function getFirstLetter(){
    return extractValue($('#id_acronym_0'));
}


function getAcronym(){
    return extractValue($('#id_acronym_1'));
}


function getPartimCharacter(){
    return extractValue($('#id_acronym_2'));
}


function callbackAcronymValidation(data){
    if (!data['valid']) {
        setErrorMessage(trans_invalid_acronym, '#id_acronym_0');
    } else if (data['existed_acronym'] && !data['existing_acronym']) {
        setWarningMessage(trans_existed_acronym + data['last_using'], '#id_acronym_0');
    } else if (data['existing_acronym']) {
        setErrorMessage(trans_existing_acronym + data['first_using'], '#id_acronym_0');
    }
}


function setErrorMessage(text, element){
    parent = $(element).closest(".acronym-group");
    parent.addClass('has-error');
    parent.append("<div class='help-block'>" + text + "</div>");
}

function setWarningMessage(text, element){
    parent = $(element).closest(".acronym-group");
    parent.addClass('has-warning');
    parent.append("<div class='help-block'>" + text + "</div>");
}


function validateAcronymAjax(url, acronym, year_id, callback) {
    /**
    * This function will check if the acronym exist or have already existed
    **/
    queryString = "?acronym=" + acronym + "&year_id=" + year_id;
    $.ajax({
       url: url + queryString
    }).done(function(data){
        callback(data);
    });
}

$(document).ready(function() {
    $(function () {
        $('#LearningUnitYearForm').validate();
    });
    $.extend($.validator.messages, {
        required: trans_field_required,
        min: trans_field_min,
        max: trans_field_max
    });

    document.getElementById('id_additional_requirement_entity_1').disabled = !isLearningUnitSubtypeFull()
        || isValueEmpty('id_requirement_entity')
        || isDisabledField('id_requirement_entity');
    document.getElementById('id_additional_requirement_entity_2').disabled = !isLearningUnitSubtypeFull()
        || isValueEmpty('id_additional_requirement_entity_1')
        || isDisabledField('id_additional_requirement_entity_1');

    $('#id_acronym_0').change(validate_acronym);
    $('#id_acronym_1').change(validate_acronym);

    InitialAcronym = getCompleteAcronym();

    $('#id_academic_year').change(validate_acronym);
    $("#LearningUnitYearForm").submit(function( event ) {
        if (!window.valid_acronym) {
            $("#id_acronym_1").focus();
        }
        return window.valid_acronym;
    });

    $('#learning_unit_year_add').click(function() {
        if(window.acronym_already_used){
            $form = $("#LearningUnitYearForm");
            $form.validate();
            var formIsValid = $form.valid();
            if(formIsValid){
              $("#prolongOrCreateModal").modal();
            }
        } else {
            $("#LearningUnitYearForm").submit();
        }
    });
});