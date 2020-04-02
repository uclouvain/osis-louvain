const internship = "INTERNSHIP";
const LEARNING_UNIT_FULL_SUBTYPE = "FULL";
const trans_existed_acronym = gettext('Existed code for ');
const trans_existing_acronym = gettext('Existing code in ');
const trans_invalid_acronym = gettext('Invalid code');
const trans_field_required = gettext('This field is required');
const trans_field_min = gettext('Please enter a value greater than or equal to 0.');
const trans_field_max = gettext('Please enter a value less than or equal to 500.');
const trans_field_step = gettext('Please enter a value that is a multiple of 0.5.');


var form = $('#LearningUnitYearForm').closest("form");
var InitialAcronym;


function isLearningUnitSubtypeFull(){
   return learning_unit_current_subtype === LEARNING_UNIT_FULL_SUBTYPE;
}


function isValueEmpty(html_id){
    return document.getElementById(html_id).value === ""
}


function isDisabledField(html_id){
    return $("#"+html_id).is(':disabled');
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
        if (id === 'id_additional_requirement_entity_2') {
            $('#select2-id_additional_requirement_entity_2-container').empty();
        }
        document.getElementById(id).disabled = true;
    }
    else if (!disable_only){
        document.getElementById(id).disabled = false;
    }
}

function clearAdditionalEntity(id){
    if (id === 'id_additional_requirement_entity_1') {
            $('#select2-id_additional_requirement_entity_1-container').empty();
    }
    if (id === 'id_additional_requirement_entity_2') {
            $('#select2-id_additional_requirement_entity_2-container').empty();
    }
}

function validate_acronym() {
    cleanErrorMessage();
    let newAcronym = getCompleteAcronym();
    if (newAcronym.length > 1 && newAcronym !== InitialAcronym) {
        let validationUrl = $('#LearningUnitYearForm').data('validate-url');
        let year_id = $('#id_academic_year').val();
        validateAcronymAjax(validationUrl, newAcronym, year_id, callbackAcronymValidation);
    }
}


function cleanErrorMessage(){
    parent = $("#id_acronym_0").closest(".acronym-group");
    parent.removeClass('has-error');
    parent.removeClass('has-warning');
    parent.find(".help-block").remove();
    parent.find(".has-error").removeClass('has-error');
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
    if (parent.find('.help-block').length === 0) {
        parent.addClass('has-error');
        parent.append("<div class='help-block'>" + text + "</div>");
    }
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
        $('#LearningUnitYearForm').validate({
            //It allow the specify a field that must not be pre-valided on client side
            ignore: ".ignore-js-validator input"
        });
        if(isDisabledField('allocation_entity')){
            document.getElementById('id_allocation_entity-country').disabled = true;
        };
    });
    $.extend($.validator.messages, {
        required: trans_field_required,
        min: trans_field_min,
        max: trans_field_max,
        step: trans_field_step,
        url: gettext("Please enter a valid URL."),
    });

    if ($("#id_container_type").is(':enabled')) {
        showInternshipSubtype();
    }

    document.getElementById('id_additional_requirement_entity_1').disabled = !isLearningUnitSubtypeFull()
        || isValueEmpty('id_requirement_entity')
        || isDisabledField('id_requirement_entity');
    document.getElementById('id_additional_entity_1_country').disabled = !isLearningUnitSubtypeFull()
        || isValueEmpty('id_requirement_entity')
        || isDisabledField('id_requirement_entity');
    document.getElementById('id_additional_requirement_entity_2').disabled = !isLearningUnitSubtypeFull()
        || isValueEmpty('id_additional_requirement_entity_1')
        || isDisabledField('id_additional_requirement_entity_1');
    document.getElementById('id_additional_entity_2_country').disabled = !isLearningUnitSubtypeFull()
        || isValueEmpty('id_additional_requirement_entity_1')
        || isDisabledField('id_additional_requirement_entity_1');
    document.getElementById('id_component-0-repartition_volume_additional_entity_1').disabled = isValueEmpty('id_additional_requirement_entity_1');
    document.getElementById('id_component-1-repartition_volume_additional_entity_1').disabled = isValueEmpty('id_additional_requirement_entity_1');
    document.getElementById('id_component-0-repartition_volume_additional_entity_2').disabled = isValueEmpty('id_additional_requirement_entity_2');
    document.getElementById('id_component-1-repartition_volume_additional_entity_2').disabled = isValueEmpty('id_additional_requirement_entity_2');

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

    $("button[name='learning_unit_year_add']").click(function(event) {
        event.preventDefault();
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
    $('#id_credits').removeAttr('required');
});
