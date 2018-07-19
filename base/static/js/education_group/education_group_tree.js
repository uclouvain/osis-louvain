function switchTreeVisibility() {
    var newTreeVisibility = (sessionStorage.getItem('treeVisibility') === '0') ? '1' : '0';
    sessionStorage.setItem('treeVisibility', newTreeVisibility);
    showOrHideTree()
}

function showOrHideTree() {
    if (sessionStorage.getItem('treeVisibility') === "0") {
        modifyPanelAttribute("none", "col-md-0", "col-md-12");
    } else {
        modifyPanelAttribute("block", "col-md-3", "col-md-9");
    }
}


function modifyPanelAttribute(collapse_style_display, panel_collapse_class, panel_data_class){
    document.getElementById('collapse').style.display = collapse_style_display;
    document.getElementById('panel-collapse').className = panel_collapse_class;
    document.getElementById('panel-data').className = panel_data_class;
}


$(document).ready(function () {
    var $documentTree = $('#panel_file_tree');
    $documentTree.bind("loaded.jstree", function (event, data) {
        data.instance.open_all();
    });
    $documentTree.bind("changed.jstree", function (event, data) {
        document.location.href = data.node.a_attr.href;
    });

    $documentTree.jstree({
        "core" : {
           "check_callback" : true
        },
        "plugins" : [ "contextmenu" ],
        "contextmenu" : {
            "select_node": false,
            "items" : {
              "select" : {
                  "label" : gettext("Select"),
                  "action" : function (data) {
                    var inst = $.jstree.reference(data.reference),
                        obj = inst.get_node(data.reference);

                    $.ajax({
                        url: '../select_education_group/',
                        data: {'education_group_id' : obj.li_attr.id},
                        type: 'get',
                        dataType: 'json',
                    });

                    alert('Select : ' + obj.li_attr.id)
                  },
                  "icon": "fa fa-check-square"
              },
              "attach" : {
                 "label" : gettext("Attach"),
                 "action" : function (data) {
                    var inst = $.jstree.reference(data.reference),
                        obj = inst.get_node(data.reference);
                    alert('Attach : ' + obj.li_attr.id)
                  },
                  "icon": "fa fa-paperclip"
              },
              "detach" : {
                 "label" : gettext("Detach"),
                 "action" : function (data) {
                    var inst = $.jstree.reference(data.reference),
                        obj = inst.get_node(data.reference);
                    alert('Detach : ' + obj.li_attr.id)
                  },
                  "icon": "fa fa-cut"
              }
            }
        }
    });

    $("#tree_open_all").click(function(){
        $documentTree.jstree("open_all");

    });

    $("#tree_close_all").click(function(){
        $documentTree.jstree("close_all");

    });

    showOrHideTree();

});