$(document).ready(function () {
    // open or hide the sidebar.
    let treeVisibility = localStorage.getItem("treeVisibility") || "0";
    if (treeVisibility === "1") {
        openNav();
    } else {
        closeNav();
    }

    let $documentTree = $('#panel_file_tree');

    $documentTree.bind("state_ready.jstree", function (event, data) {
        // Bind the redirection only when the tree is ready,
        // however, it reload the page during the loading
        $documentTree.bind("select_node.jstree", function (event, data) {
            document.location.href = data.node.a_attr.href;
        });
        // if the tree has never been loaded, execute close_all by default.
        if ($.vakata.storage.get(data.instance.settings.state.key) === null) {
            $(this).jstree('close_all');
        }
    });

    function get_data_from_tree(data) {
        let inst = $.jstree.reference(data.reference),
            obj = inst.get_node(data.reference);

        return {
            group_element_year_id: obj.a_attr.group_element_year,
            element_id: obj.a_attr.element_id,
            element_type: obj.a_attr.element_type,
            has_prerequisite: obj.a_attr.has_prerequisite,
            is_prerequisite: obj.a_attr.is_prerequisite,
            view_url: obj.a_attr.href,
            attach_url: obj.a_attr.attach_url,
            detach_url: obj.a_attr.detach_url,
            modify_url: obj.a_attr.modify_url,
            attach_disabled: obj.a_attr.attach_disabled,
            detach_disabled: obj.a_attr.detach_disabled,
            modification_disabled: obj.a_attr.modification_disabled
        };
    }

    function build_url_data(element_id, group_element_year_id, action) {
        var data = {
            'root_id': root_id,
            'element_id': element_id,
            'group_element_year_id': group_element_year_id,
            'action': action,
            'source': url_resolver_match
        };
        return jQuery.param(data);
    }

    $documentTree.jstree({
            "core": {
                "check_callback": true,
                "data": tree,
            },
            "plugins": [
                "contextmenu",
                // Plugin to save the state of the node (collapsed or not)
                "state",
                "search",
            ],
            "state": {
                // the key is important if you have multiple trees in the same domain
                // The key includes the root_id
                "key": location.pathname.split('/', 3).join('/'),
                "opened": true,
                "selected": false,
            },
            "contextmenu": {
                "select_node": false,
                "items": function($node){
                    return {
                        "select": {
                            "label": gettext("Select"),
                            "action": function (data) {
                                let __ret = get_data_from_tree(data);
                                let element_id = __ret.element_id;
                                let group_element_year_id = __ret.group_element_year_id;
                                $.ajax({
                                    url: management_url,
                                    dataType: 'json',
                                    data: {
                                        'element_id': element_id,
                                        'group_element_year_id': group_element_year_id,
                                        'action': 'select'
                                    },
                                    type: 'POST',
                                    success: function (jsonResponse) {
                                        displayInfoMessage(jsonResponse, 'message_info_container')
                                    }
                                });
                            }
                        },

                        "modify": {
                            "label": gettext("Modify"),
                            "action": function (data) {
                                let __ret = get_data_from_tree(data);

                                $('#form-modal-ajax-content').load(__ret.modify_url, function (response, status, xhr) {
                                    if (status === "success") {
                                        $('#form-ajax-modal').modal('toggle');
                                        let form = $(this).find('form').first();
                                        formAjaxSubmit(form, '#form-ajax-modal');
                                    } else {
                                        window.location.href = __ret.modify_url
                                    }
                                });
                            },
                            "title": $node.a_attr.modification_msg,
                            "_disabled": function (data) {
                                let __ret = get_data_from_tree(data);
                                // tree's root cannot be edit (no link with parent...)
                                return __ret.modification_disabled === true;
                            }
                        },

                        "attach": {
                            "label": gettext("Attach"),
                            "separator_before": true,
                            "action": function (data) {
                                let __ret = get_data_from_tree(data);

                                $('#form-modal-ajax-content').load(__ret.attach_url, function (response, status, xhr) {
                                    if (status === "success") {
                                        $('#form-ajax-modal').modal('toggle');
                                        let form = $(this).find('form').first();
                                        formAjaxSubmit(form, '#form-ajax-modal');
                                    } else {
                                        window.location.href = __ret.attach_url
                                    }
                                });
                            },
                            "title": $node.a_attr.attach_msg,
                            "_disabled": function (data) {
                                let __ret = get_data_from_tree(data);
                                return __ret.attach_disabled === true;
                            }
                        },

                        "detach": {
                            "label": gettext("Detach"),
                            "action": function (data) {
                                let __ret = get_data_from_tree(data);
                                if (__ret.detach_url === '#') {
                                    return;
                                }

                                $('#form-modal-ajax-content').load(__ret.detach_url, function (response, status, xhr) {
                                    if (status === "success") {
                                        $('#form-ajax-modal').modal('toggle');

                                        let form = $(this).find('form').first();
                                        formAjaxSubmit(form, '#form-ajax-modal');
                                    } else {
                                        window.location.href = __ret.detach_url
                                    }

                                });
                            },
                            "title": $node.a_attr.detach_msg,
                            "_disabled": function (data) {
                                let __ret = get_data_from_tree(data);
                                // tree's root and learning_unit having/being prerequisite(s) cannot be detached
                                return __ret.detach_disabled === true;
                            }
                        },

                        "open_all": {
                            "separator_before": true,
                            "label": gettext("Open all"),
                            "action": function (node) {
                                let tree = $("#panel_file_tree").jstree(true);
                                tree.open_all(node.reference)
                            }
                        },
                        "close_all": {
                            "label": gettext("Close all"),
                            "action": function (node) {
                                let tree = $("#panel_file_tree").jstree(true);
                                tree.close_all(node.reference);
                            }
                        }
                    };
                }
            }
        }
    );

    var to = false;
    $('#search_jstree').keyup(function () {
        if (to) {
            clearTimeout(to);
        }
        to = setTimeout(function () {
            var v = $('#search_jstree').val();
            $documentTree.jstree(true).search(v);
        }, 250);
    });
});

function toggleNav() {
    let treeVisibility = localStorage.getItem("treeVisibility") || "0";
    if (treeVisibility === "0") {
        openNav();
    } else {
        closeNav();
    }
}

function openNav() {
    let size = localStorage.getItem("sidenav_size") || "300px";
    document.getElementById("mySidenav").style.width = size;
    document.getElementById("main").style.marginLeft = size;
    localStorage.setItem("treeVisibility", "1");

}

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
    document.getElementById("main").style.marginLeft = "0";
    localStorage.setItem("treeVisibility", "0");
}

const min = 300;
const max = 1000;
const mainmin = 600;

$('#split-bar').mousedown(function (e) {
    e.preventDefault();
    $(document).mousemove(function (e) {
        e.preventDefault();

        let sidebar = $("#mySidenav");
        let x = e.pageX - sidebar.offset().left;
        if (x > min && x < max && e.pageX < ($(window).width() - mainmin)) {
            sidebar.css("width", x);
            $('#main').css("margin-left", x);
        }
        localStorage.setItem("sidenav_size", sidebar.width().toString() + "px")
    })
});
$(document).mouseup(function () {
    $(document).unbind('mousemove');
});

