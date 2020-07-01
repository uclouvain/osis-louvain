const PANEL_TREE_MIN_WIDTH = 300;
const PANEL_TREE_MAX_WIDTH = 1000;
const PANEL_TREE_MAIN_MIN_WIDTH = 600;


$(document).ready(function () {
    setListenerForCopyElements();
    setListenerForCutElements();
    setListnerForClearClipboard();

    let $documentTree = $('#panel_file_tree');
    if ($documentTree.length) {
        const copy_element_url = $documentTree.attr("data-copyUrl");
        const cut_element_url = $documentTree.attr("data-cutUrl");

        setNavVisibility();
        initializeJsTree($documentTree, cut_element_url, copy_element_url);
        setResearchTimeOut($documentTree);
    }
});


function setListenerForCopyElements() {
    $(".copy-element").click(function (event) {
        const url = event.target.dataset.url;
        const element_code = event.target.dataset.element_code;
        const element_year = event.target.dataset.element_year;
        handleCopyAction(url, element_code, element_year);
        event.preventDefault();
    });
}

function setListenerForCutElements() {
    $(".cut-element").click(function (event) {
        const url = event.target.dataset.url;
        const element_code = event.target.dataset.element_code;
        const element_year = event.target.dataset.element_year;
        const path_to_detach_from = event.target.dataset.path;
        handleCutAction(url, element_code, element_year, path_to_detach_from);
        event.preventDefault();
    });
}

function setListnerForClearClipboard() {
    const clearClipboardsElements = document.getElementsByClassName("clear-clipboard");
    for (let i = 0; i < clearClipboardsElements.length; i++) {
        clearClipboardsElements[i].addEventListener("click", clearClipboardListener);
    }
}

function setResearchTimeOut($documentTree) {
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
}


function setNavVisibility() {
    let treeVisibility = localStorage.getItem("treeVisibility") || "0";
    if (treeVisibility === "1") {
        openNav();
        adaptTreeOnFooter();
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

function toggleNav() {
    let treeVisibility = localStorage.getItem("treeVisibility") || "0";
    if (treeVisibility === "0") {
        openNav();
    } else {
        closeNav();
    }
}

$('#split-bar').mousedown(function (e) {
    e.preventDefault();
    $(document).mousemove(function (e) {
        e.preventDefault();

        let sidebar = $("#mySidenav");
        let x = e.pageX - sidebar.offset().left;
        if (x > PANEL_TREE_MIN_WIDTH && x < PANEL_TREE_MAX_WIDTH && e.pageX < ($(window).width() - PANEL_TREE_MAIN_MIN_WIDTH)) {
            sidebar.css("width", x);
            $('#main').css("margin-left", x);
        }
        localStorage.setItem("sidenav_size", sidebar.width().toString() + "px")
    })
});

$(document).mouseup(function () {
    $(document).unbind('mousemove');
});

$("a[id^='quick-search']").click(function (event) {
    event.preventDefault();
    $(this).attr('data-url', $('#j1_1_anchor').attr('search_url'));
});


$("#scrollableDiv").on("scroll", function() {
    saveScrollPosition(tree);
});

function saveScrollPosition(tree) {
    const rootId = tree["id"];
    const scrollPosition = $("#scrollableDiv")[0].scrollTop
    const storageValue = {}
    storageValue[rootId] = scrollPosition
    localStorage.setItem('scrollpos', JSON.stringify(storageValue));
}


function scrollToPositionSaved(tree) {
    const rootId = tree["id"];
    const storageValue = JSON.parse(localStorage.getItem('scrollpos'));
    let scrollPosition = 0;
    if (storageValue !== null && rootId in storageValue) {
        scrollPosition = storageValue[rootId];
    }
    document.getElementById('scrollableDiv').scrollTo(0, scrollPosition);
}


$(window).scroll(function() {
    adaptTreeOnFooter();
});


function adaptTreeOnFooter() {
    if (checkVisible !== undefined && checkVisible($('.footer'))) {
        $('.side-container').css("height", "calc(100% - 100px)");
    } else {
        $('.side-container').css("height", "calc(100% - 50px)");
    }
}

function handleCutAction(cut_url, element_code, element_year, path_to_detach) {
    $.ajax({
        url: cut_url,
        dataType: 'json',
        data: {
            'element_code': element_code,
            'element_year': element_year,
            'path_to_detach': path_to_detach
        },
        type: 'POST',
        success: function (jsonResponse) {
            displayInfoMessage(jsonResponse, 'clipboard');
        }
    });
}

function handleCopyAction(copy_url, element_code, element_year) {
    $.ajax({
        url: copy_url,
        dataType: 'json',
        data: {
            'element_code': element_code,
            'element_year': element_year
        },
        type: 'POST',
        success: function (jsonResponse) {
            if (document.getElementById("clipboard")) {
                displayInfoMessage(jsonResponse, 'clipboard');
            } else {
                displayInfoMessage(jsonResponse, "message_info_container");
            }
        }
    });
}


function clearClipboardListener(event) {
    const clear_clipboard_url = event.currentTarget.dataset.url;
    $.ajax({
        url: clear_clipboard_url,
        type: 'POST',
        success: function () {
            $("#clipboard").hide();
        }
    });
}


function initializeJsTree($documentTree, cut_element_url, copy_element_url) {
    $documentTree.bind("state_ready.jstree", function (event, data) {
        // Bind the redirection only when the tree is ready,
        // however, it reload the page during the loading
        $documentTree.bind("select_node.jstree", function (event, data) {
            document.location.href = data.node.a_attr.href;
        });

        scrollToPositionSaved(tree);

        // if the tree has never been loaded, execute close_all by default.
        if ($.vakata.storage.get(data.instance.settings.state.key) === null) {
            $(this).jstree('close_all');
        }
    });

    function generateTreeKey(tree){
        const treeRootId = tree["id"];
        return `progrem_tree_state_${treeRootId}`;

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
                "key": generateTreeKey(tree),
                "opened": true,
                "selected": false,
            },
            "contextmenu": {
                "select_node": false,
                "items": function ($node) {
                    return {
                        "cut": {
                            "label": gettext("Cut"),
                            "_disabled": function (data) {
                                return !get_data_from_tree(data).group_element_year_id;
                            },
                            "action": function (data) {
                                const node_data = get_data_from_tree(data);
                                handleCutAction(cut_element_url, node_data.element_code, node_data.element_year, node_data.path)
                            }
                        },

                        "copy": {
                            "label": gettext("Copy"),
                            "action": function (data) {
                                const node_data = get_data_from_tree(data);
                                handleCopyAction(copy_element_url, node_data.element_code, node_data.element_year)
                            }
                        },

                        "paste": {
                            "label": gettext("Paste"),
                            "action": function (data) {
                                let __ret = get_data_from_tree(data);

                                $('#form-modal-ajax-content').load(__ret.paste_url, function (response, status, xhr) {
                                    if (status === "success") {
                                        $('#form-ajax-modal').modal('toggle');
                                        let form = $(this).find('form').first();
                                        formAjaxSubmit(form, '#form-ajax-modal');
                                    } else {
                                        window.location.href = __ret.paste_url
                                    }
                                });
                            },
                            "title": $node.a_attr.attach_msg,
                            "_disabled": function (data) {
                                let __ret = get_data_from_tree(data);
                                return __ret.paste_url == null;
                            }
                        },

                        "detach": {
                            "label": gettext("Detach"),
                            "separator_before": true,
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
                                return __ret.detach_url == null;
                            }
                        },

                        "modify": {
                            "label": gettext("Modify the link"),
                            "separator_before": true,
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
                                return __ret.modify_url == null;
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
                        },
                        "search": {
                            "separator_before": true,
                            "label": gettext("Search"),
                            "data-modal_class": "modal-lg",
                            "action": function (data) {
                                let __ret = get_data_from_tree(data);

                                document.getElementById("modal_dialog_id").classList.add("modal-lg");

                                $('#form-modal-ajax-content').load(__ret.search_url, function (response, status, xhr) {
                                    if (status === "success") {
                                        $('#form-ajax-modal').modal('toggle');

                                        let form = $(this).find('form').first();
                                        formAjaxSubmit(form, '#form-ajax-modal');
                                    } else {
                                        window.location.href = __ret.search_url;
                                    }

                                });
                            },
                            "_disabled": function (data) {
                                let __ret = get_data_from_tree(data);
                                // if no search url should be disabled
                                return __ret.search_url == null;
                            }
                        },
                    };
                }
            }
        }
    );
}


function get_data_from_tree(data) {
    let inst = $.jstree.reference(data.reference),
        obj = inst.get_node(data.reference);

    return {
        group_element_year_id: obj.a_attr.group_element_year,
        element_id: obj.a_attr.element_id,
        element_type: obj.a_attr.element_type,
        element_code: obj.a_attr.element_code,
        element_year: obj.a_attr.element_year,
        has_prerequisite: obj.a_attr.has_prerequisite,
        is_prerequisite: obj.a_attr.is_prerequisite,
        view_url: obj.a_attr.href,
        paste_url: obj.a_attr.paste_url,
        detach_url: obj.a_attr.detach_url,
        modify_url: obj.a_attr.modify_url,
        search_url: obj.a_attr.search_url,
        path: obj.a_attr.path
    };
}
