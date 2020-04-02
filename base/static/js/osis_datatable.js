function initializeDataTable(formId, tableId, storageKey, pageNumber, itemsPerPage, ajaxUrl, columnDefs, extra){
    let domTable = $('#' + tableId);
    let options = {
        'createdRow': function (row, data, dataIndex) {
            let url = "";
            if (data['osis_url']) {
                url = data['osis_url'];
            } else {
                url = data['url'];
            }
            $(row).attr('data-id', url);
            $(row).attr('data-value', data['acronym']);
        },
        columnDefs: columnDefs,
        "stateSave": true,
        "paging" : false,
        "ordering" : true,
        "orderMulti": false,
        "order": [[1, 'asc']],
        "serverSide": true,
        "ajax" : {
            "url": ajaxUrl,
            "accepts": {
                json: 'application/json'
            },
            "type": "GET",
            "dataSrc": "object_list",
            "data": function (d){
                let querystring = getDataAjaxTable(formId, domTable, d, pageNumber);
                querystring["paginator_size"] = itemsPerPage;
                return querystring;
            },
            "traditional": true
        },
        "info"  : false,
        "searching" : false,
        'processing': true,
        "language": {
            "oAria": {
                "sSortAscending":  gettext("activate to sort column ascending"),
                "sSortDescending": gettext("activate to sort column descending")
            },
            'processing': gettext("Loading...")
        }
    };
    return domTable.DataTable($.extend(true, {}, options, extra));
}


function outputAnchorOuterHtml(urlPath, textContent){
    const anchor = document.createElement("a");
    anchor.setAttribute("href", urlPath);
    anchor.textContent = textContent;
    return anchor.outerHTML;
}
