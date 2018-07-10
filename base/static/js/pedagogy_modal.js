$(".pedagogy-edit-btn").click(load_form);
$(".teaching-material-delete-btn").click(load_form);
$(".teaching-material-edit-btn").click(load_form);
$(".teaching-material-create-btn").click(load_form);
$(".mobility-modality-edit-btn").click(load_form);

// This function will load the form into a modal
function load_form(event) {
    event.preventDefault();
    var form_url = $(this).data("form");
    var modal = $("#pedagogy_edit");
    modal.load(form_url, function(responseText, textStatus, XMLHttpRequest){
        if(textStatus == 'error') {
           window.location.replace(form_url);
        } else {
            $(this).modal('show');
        }
    });
    return false;
}