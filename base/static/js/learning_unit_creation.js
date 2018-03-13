const internship = "INTERNSHIP";
const LEARNING_UNIT_FULL_SUBTYPE = "FULL";

var form = $('#LearningUnitYearForm').closest("form");


function isLearningUnitSubtypeFull(){
    if(document.getElementById('id_subtype') !== null){

        return document.getElementById('id_subtype').value === LEARNING_UNIT_FULL_SUBTYPE
    }
    else if (learning_unit_current_subtype !== undefined){
        return learning_unit_current_subtype === LEARNING_UNIT_FULL_SUBTYPE;
    }
    return true;
}


function isValueEmpty(html_id){
    return document.getElementById(html_id).value == ""
}


function isDisabledField(html_id){
    return document.getElementById(html_id).disabled == true
}


function showInternshipSubtype(){
    if (isLearningUnitSubtypeFull() && document.getElementById('id_internship_subtype')) {
        var container_type_value = document.getElementById('id_container_type').value;
        var value_not_internship = container_type_value != internship;
        var labelElem = $('#lbl_internship_subtype')

        document.getElementById('id_internship_subtype').disabled = value_not_internship;
        if (value_not_internship) {
            $('#id_internship_subtype')[0].selectedIndex = 0;
            $('#lbl_internship_subtype_error').empty(); // Remove error message if exist
            labelElem.text(labelElem.text().replace('*','')) // Remove asterix in order to indicate field not required
        } else {
             labelElem.append('*'); // Add asterix in order to indicate field required
        }
    }
}

function updateAdditionalEntityEditability(elem, id, disable_only){
    var empty_element = elem == "";
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
    var validationUrl = $('#LearningUnitYearForm').data('validate-url');
    var year_id = $('#id_academic_year').val();
    validateAcronymAjax(validationUrl, newAcronym, year_id, callbackAcronymValidation);
}


function cleanErrorMessage(){
    $('#acronym_message').removeClass("error-message").text("");
}


function getCompleteAcronym(){
    var acronym = getFirstLetter() + getAcronym() + getPartimCharacter();
    return acronym.toUpperCase();
}

function extractValue(domElem){
    return (domElem && domElem.val()) ? domElem.val(): "";
}


function getFirstLetter(){
    return extractValue($('#id_first_letter'));
}


function getAcronym(){
    return extractValue($('#id_acronym'));
}


function getPartimCharacter(){
    return extractValue($('#hdn_partim_character'));
}


function callbackAcronymValidation(data){
    if (!data['valid']) {
        setErrorMessage(trans_invalid_acronym, '#acronym_message');
    } else if (data['existed_acronym'] && !data['existing_acronym']) {
        setWarningMessage(trans_existed_acronym + data['last_using'], '#acronym_message');
    } else if (data['existing_acronym']) {
        setErrorMessage(trans_existing_acronym + data['first_using'], '#acronym_message');
    }
}


function setErrorMessage(text, element){
    $(element).addClass("error").text(text);
    $(element).css("color","red");
}

function setWarningMessage(text, element){
    $(element).addClass("warning").text(text);
    $(element).css("color","orange");
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

    showInternshipSubtype();
    document.getElementById('id_additional_requirement_entity_1').disabled = !isLearningUnitSubtypeFull() || isValueEmpty('id_requirement_entity') || isDisabledField('id_requirement_entity');
    document.getElementById('id_additional_requirement_entity_2').disabled = !isLearningUnitSubtypeFull() || isValueEmpty('id_additional_requirement_entity_1') || isDisabledField('id_additional_requirement_entity_1');

    $('#id_acronym').change(validate_acronym);
    $('#id_academic_year').change(validate_acronym);
    $("#LearningUnitYearForm").submit(function( event ) {
        if (!window.valid_acronym) {
            $("#id_acronym").focus();
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