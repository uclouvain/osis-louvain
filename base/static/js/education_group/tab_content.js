$(document).ready(function () {
    $('#minor_major_option_table').DataTable({
        columnDefs: [
            { orderable: false, targets: [4] }
        ],
        "stateSave": true,
        "paging" : false,
        "ordering" : true,
        "order": [[ 0, "asc" ]],
        "info"  : false,
        "searching" : false,
        "language": {
            "oAria": {
                "sSortAscending":  "{% trans 'datatable_sortascending'%}",
                "sSortDescending": "{% trans 'datatable_sortdescending'%}"
            }
        }
    });
});