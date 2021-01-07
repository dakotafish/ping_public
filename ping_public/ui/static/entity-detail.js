
function updateAttrDisplay() {
    // I need a better solution for this.
    console.log('Change Event Fired..');
    let ASSERTION = 'ASSERTION';
    let STRING = 'STRING';
    let QUERY = 'QUERY';
    //attrForm['id_token_attribute_value'].parentElement.style.display = 'none';
    let attributeConfigurations = document.getElementsByClassName('attributeConfiguration');
    for (var attributeConfig of attributeConfigurations) {
        let attrForm = attributeConfig.firstElementChild;
        let attributeType = attrForm['attribute_type'].value;
        console.log('attributeType = ' + attributeType);
        if (attributeType == ASSERTION) {
            // hide id_token_attribute_value, id_query, id_query_parameters
            attrForm['id_token_attribute_value'].parentElement.style.display = 'none';
            attrForm['id_query'].parentElement.style.display = 'none';
            attrForm['id_query_parameters'].parentElement.style.display = 'none';
            // show id_attribute_type, id_saml_attribute_name, id_include_in_token, id_token_attribute_name
            attrForm['id_attribute_type'].parentElement.style.display = '';
            attrForm['id_saml_attribute_name'].parentElement.style.display = '';
            attrForm['id_include_in_token'].parentElement.style.display = '';
            attrForm['id_token_attribute_name'].parentElement.style.display = '';
        } else if (attributeType == STRING) {
            // hide id_saml_attribute_name, id_query, id_query_parameters
            attrForm['id_saml_attribute_name'].parentElement.style.display = 'none';
            attrForm['id_query'].parentElement.style.display = 'none';
            attrForm['id_query_parameters'].parentElement.style.display = 'none';
            // show id_attribute_type, id_include_in_token, id_token_attribute_name, id_token_attribute_value
            attrForm['id_attribute_type'].parentElement.style.display = '';
            attrForm['id_include_in_token'].parentElement.style.display = '';
            attrForm['id_token_attribute_name'].parentElement.style.display = '';
            attrForm['id_token_attribute_value'].parentElement.style.display = '';
        } else if (attributeType == QUERY) {
            // hide id_token_attribute_value, id_saml_attribute_name
            attrForm['id_token_attribute_value'].parentElement.style.display = 'none';
            attrForm['id_saml_attribute_name'].parentElement.style.display = 'none';
            // show id_attribute_type, id_include_in_token, id_token_attribute_name, id_query, id_query_parameters
            attrForm['id_attribute_type'].parentElement.style.display = '';
            attrForm['id_include_in_token'].parentElement.style.display = '';
            attrForm['id_token_attribute_name'].parentElement.style.display = '';
            attrForm['id_query'].parentElement.style.display = '';
            attrForm['id_query_parameters'].parentElement.style.display = '';
        }
    }
}


async function submitForm(event) {
    console.log("----submitting form-----")
    event.preventDefault();
    //let submittedForm = event.target;
    let submittedForm = event.target.parentElement;
    let url = submittedForm.action;
    let formData = new FormData(submittedForm);
    let submitButton = submittedForm.querySelector('input[type="submit"]');
    let response = await fetch(url,
        {
        method: 'POST',
        body: formData
        });

    if (response.ok) {
        let responseText = await response.text();
        submitButton.insertAdjacentHTML('afterend', `<span id="timedSpan" style="color: green"> ${responseText} </span`);
        setTimeout(() => {
            //let timedSpan = document.getElementById("timedSpan").innerHTML = "";
            document.getElementById("timedSpan").remove();
        }, 3000);
        console.log(responseText);
    } else {
        let responseText = await response.text();
        submitButton.insertAdjacentHTML('afterend', `<span id="timedSpan" style="color: red"> ${responseText} </span`);
        setTimeout(() => {
            //let timedSpan = document.getElementById("timedSpan").innerHTML = "";
            document.getElementById("timedSpan").remove();
        }, 3000);
    }
}

async function submitTableForm(event) {
    console.log("-----submitting table row as form------");
    event.preventDefault();
    let button = event.currentTarget;
    let target = button.formTarget;
    let buttonCell = button.parentElement;
    let tableRow = button.parentElement.parentElement.cloneNode(deep=true);
    let tableRowForm = document.createElement('form');
    tableRowForm.replaceChildren(tableRow);
    let formData = new FormData(tableRowForm);
    let response = await fetch(target,
        {method: 'POST',
        body: formData}
    );
    if (response.ok) {
        //let responseText = await response.text();
        let responseBody = await response.json();
        buttonCell.insertAdjacentHTML('afterend', `<span id="timedSpan" style="color: green"> ${responseBody.MESSAGE} </span`);
        setTimeout(() => {
            document.getElementById("timedSpan").remove();
            //let timedSpan = document.getElementById("timedSpan").innerHTML = "";
            //console.log(document.getElementById("timedSpan"));
        }, 3000);
        if (target.includes("create-new")) {
            // blank forms use a target url of create-new
            // once it's been created we change that target to the update url returned from the view
            button.formTarget = responseBody.UPDATE_URL;
        }
    } else {
        let responseText = await response.text();
        buttonCell.insertAdjacentHTML('afterend', `<span id="timedSpan" style="color: red"> ${responseText} </span`);
        setTimeout(() => {
            document.getElementById("timedSpan").remove();
            //let timedSpan = document.getElementById("timedSpan").innerHTML = "";
        }, 3000);
    }
}



async function getNewForm(button) {
    console.log('----getting new form---')
    event.preventDefault();
    let target = button.getAttribute("target");
    let parentElement = button.parentElement;
    let response = await fetch(target);
    if (response.ok) {
        let responseText = await response.text();
        console.log(responseText);
        parentElement.insertAdjacentHTML('afterend', responseText);
    }
    //addFormSubmitEventListeners();
}


async function getNewFormForTable(button) {
    event.preventDefault();
    let target = button.getAttribute("target");
    let tableRows = button.parentElement.getElementsByTagName("tr");
    let lastTableRow = tableRows[tableRows.length - 1];
    let response = await fetch(target);
    if (response.ok) {
        let responseText = await response.text();
        console.log(responseText);
        lastTableRow.insertAdjacentHTML('afterend', responseText);
    }
    //addFormSubmitEventListeners();
}


//function addFormSubmitEventListeners() {
//    let classNames = ['attributeConfiguration', 'destinationConfiguration'];
//    for (let className of classNames) {
//        let divs = document.getElementsByClassName(className);
//        for (let div of divs) {
//            forms = div.getElementsByTagName('form');
//            for (let form of forms) {
//                form.addEventListener("submit", submitForm);
//            }
//        }
//    }
//    let tableClassNames = ['relaystateConfiguration'];
//    for (let className of tableClassNames) {
//        let divs = document.getElementsByClassName(className);
//        for (let div of divs) {
//            let table = div.getElementsByTagName('table')[0];
//            let buttons = table.querySelectorAll('input[type="submit"]');
//            for (let button of buttons) {
//                button.addEventListener("click", submitTableForm);
//            }
//        }
//    }
//}


//addFormSubmitEventListeners();
//let form = document.entityForm;
//form.addEventListener("submit", submitForm);




//function addAttrTypeEventListeners() {
//    let attributeTypeElements = document.getElementsByName("attribute_type");
//    for (var element of attributeTypeElements) {
//        element.setAttribute('onchange', 'updateAttrDisplay()');
//    }
//}
//
//addAttrTypeEventListeners();

//function submitForm(event){
//    event.preventDefault();
//    let submittedForm = event.target;
//    let url = submittedForm.action;
//    let formData = new FormData(submittedForm);
//    fetch(url, {
//    method: 'POST',
//    body: formData
//    })
//    .then(response => {
//        console.log('..Received the response...')
//        console.log(response.status)
//        console.log(response)
//        console.log(response.text())
//        console.log('----')
//        console.log(response.PromiseResult)
//        console.log('----')
//    })
//    .then(result => {
//        console.log('Success: ', result);
//    });
//}