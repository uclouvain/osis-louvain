$(document).ready(function () {
    highlightFormTabsWithError()
});

function highlightFormTabsWithError(){
    const formTabsUl = document.getElementsByClassName("form-tab");
    for (const tabUlElement of formTabsUl){
        const tabContentElement = getTabContentElementFromTabUl(tabUlElement);
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
    return tabContentElement.getElementsByClassName('has-error').length > 0 || tabContentElement.getElementsByClassName('has-warning').length > 0
}

function highlightTabUl(tabUlElement){
    tabUlElement.classList.add("contains-error");
}