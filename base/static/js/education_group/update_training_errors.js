$(document).ready(function () {
    deprecatedHighlightsFormTabsWithError()
    highlightFormTabsWithError()
});

function deprecatedHighlightsFormTabsWithError(){
    const tabs = ['identification', 'content', 'diploma'];
    tabs.forEach(function (tab_name) {
        const tab = document.getElementById('tab_' + tab_name);
        let spn_tab_errors = $("#spn_" + tab_name + "_errors");
        spn_tab_errors.empty();
        if (tab && tab.getElementsByClassName('has-error').length > 0) {
            spn_tab_errors.empty();
            spn_tab_errors.append('<i class="fa fa-circle" aria-hidden="true"></i>')
        }
    });
}

function highlightFormTabsWithError(){
    const formTabsUl = document.getElementsByClassName("form-tab");
    for (const tabUlElement of formTabsUl){
        const tabContentElement = getTabContentElementFromTabUl(tabUlElement)
        if (doesTabContainsErrors(tabContentElement)) {
            highlightTabUl(tabUlElement)
        }
    }
}

function getTabContentElementFromTabUl(tabUlElement){
    const anchorElement = tabUlElement.getElementsByTagName("A")[0]
    const tabContentId = anchorElement.getAttribute("href").replace("#", "")
    return document.getElementById(tabContentId)
}

function doesTabContainsErrors(tabContentElement){
    return tabContentElement.getElementsByClassName('has-error').length > 0
}

function highlightTabUl(tabUlElement){
    tabUlElement.classList.add("has-error")
}