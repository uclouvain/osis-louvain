
$('a.modify-text-btn').click(function (evt) {
    evt.preventDefault();
    var url = $(this).data('form');
    var modal = $("#modify_text");
    modal.load(url, function () {
        $(this).modal('show');
    });
    return false;
});
