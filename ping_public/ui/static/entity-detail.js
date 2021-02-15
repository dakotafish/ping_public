class Form {
    constructor(eventTarget) {
        this.submitButton = eventTarget.target;
        this.targetUrl = eventTarget.url;
        this.role = eventTarget.role;
        this.action = eventTarget.action;
        this.model = eventTarget.model;
        this.modelId = eventTarget.modelId
        this.uniqueElementId = `${this.model}_${this.modelId}`;
    }

    async submitForm(method='POST', action) {
        let formData = new FormData(this.submittedForm);
        let response = await fetch(this.targetUrl,
            {
                method: method,
                body: formData,
                headers: {'X-CSRFToken': csrftoken}
            });
        if (response.ok) {
            this.responseBody = await response.json();
            this.success = true;
        } else {
            this.responseBody = await response.json();
            this.success = false;
        }
        this.displayStatusMessage();
        this.continueProcessing(action);
    };

    async deleteInstance(method='DELETE', action) {
        let message = this.getCustomDeleteMessage()
        if (message == null) {
            message = 'Are you sure you want to delete this item?'
        }
        let userConfirmation = confirm(message);

        if (userConfirmation == true && this.modelId.includes('NEW')) {
            this.success = true;
            this.responseBody = {'message': `Removing ${this.model}`};
            this.displayStatusMessage();
            this.continueProcessing('DELETE');
        } else if (userConfirmation == true) {
            let response = await fetch(this.targetUrl,
                {
                    method: method,
                    headers: {'X-CSRFToken': csrftoken}
                });
            if (response.ok) {
                this.responseBody = await response.json();
                this.success = true;
            } else {
                this.responseBody = await response.json();
                this.success = false;
            }
            this.displayStatusMessage();
            this.continueProcessing('DELETE');
        }
    };

    async fetchNewForm(method='GET') {
        let response = await fetch(this.targetUrl,
            {
                method: method,
                headers: {'X-CSRFToken': csrftoken}
            });
        if (response.ok) {
            this.responseBody = await response.json();
            this.success = true;
            this.insertNewForm()
        } else {
            this.responseBody = await response.json();
            this.success = false;
        }
    };

    removeTimedSpan() {
        setTimeout(() => {
            document.getElementById("timedSpan").remove();
        }, 3000);
    };

    displayStatusMessage(messageLocation='afterend') {
        if (this.success) {
            var html = `<span id="timedSpan" style="color: green"> ${this.responseBody.message} </span`;
        } else {
            var html = `<span id="timedSpan" style="color: red"> ${this.responseBody.message} </span`;
        }

        this.submitButton.insertAdjacentHTML(messageLocation, html);
        this.removeTimedSpan();
    };

    continueProcessing() {
        // pass
        // this method can be implemented on child classes when necessary
    };

    insertNewForm() {
        // pass
        // each form will be inserted differently so this will be implemented on child classes
    }

    getCustomDeleteMessage() {
        // pass
    }
}

class StandardForm extends Form {
    constructor(eventTarget) {
        super(eventTarget);
        this.submittedForm = document.getElementById(this.uniqueElementId);
    }
}

class CertificateForm extends Form {
    constructor(eventTarget) {
        super(eventTarget);
        this.submittedForm = document.getElementById("certificateForm");
    }

    continueProcessing(action) {
        if (action == 'CREATE-NEW') {
            // add the new certificate to the certificate table
            let certTable = document.getElementById('certificateTable');
            let lastRow = certTable.lastElementChild.lastElementChild;
            let newRow = lastRow.cloneNode(true);
            newRow.children.common_name.innerText = this.responseBody.common_name;
            newRow.children.serial_number.innerText = this.responseBody.serial_number;
            newRow.children.issue_date.innerText = this.responseBody.issue_date;
            newRow.children.expiration_date.innerText = this.responseBody.expiration_date;
            //newRow.children.downloadButton.lastElementChild.formTarget
            newRow.children.deleteButton.lastElementChild.formTarget = this.responseBody.delete_url;
            newRow.style="color: green";
            lastRow.insertAdjacentElement('afterend', newRow);
            setTimeout(() => { newRow.style="color: inherit"; }, 3000);
        } else if (action == 'DELETE') {
            // remove the deleted certificate from the certificate table
            let rowToDelete = document.getElementById(this.uniqueElementId);
            rowToDelete.remove();
        }
    }

    getCustomDeleteMessage() {
        let row = document.getElementById(this.uniqueElementId);
        let message = `Are you sure you want to delete this item?\n\t
                        CN = ${row.children.common_name.innerText}
                        Issue Date = ${row.children.issue_date.innerText}
                        Exp Date = ${row.children.expiration_date.innerText}`
        return message
    }
}

class DestinationForm extends Form {
    constructor(eventTarget, id) {
        super(eventTarget);
        this.submittedForm = eventTarget.target.parentElement.parentElement;
    }

    insertNewForm() {
        // insert the new destination form at the end of the page
        let lastElement = document.getElementById('entityContainer').lastElementChild;
        let newForm = this.responseBody['new_form'];
        lastElement.insertAdjacentHTML('afterend', newForm);
        let newDestinationForm = document.getElementById('DESTINATION_NEW');
        newDestinationForm.parentElement.scrollIntoView();
    }

    getCustomDeleteMessage() {
        let form = this.submittedForm
        let formData = new FormData(form);
        let name = formData.get('name');
        if (name == '' && this.modelId.includes('NEW')) {
            name = 'New Destination';
        }
        let message = `Are you sure you want to delete this item?\n\t
                        Destination Name = ${name}`
        return message;
    }

    continueProcessing(action) {
        if (action == 'DELETE') {
            let destinationForm = document.getElementById(this.uniqueElementId);
            let destinationContainer = destinationForm.parentElement;
            destinationContainer.remove();
        } else if (action == 'CREATE-NEW') {
            if ('unique_element_id' in this.responseBody) {
                let destinationForm = document.getElementById('DESTINATION_NEW');
                destinationForm.id = this.responseBody.unique_element_id;
            }
            if ('update_url' in this.responseBody) {
                let saveButton = document.getElementById('NEW_DESTINATION_SAVE_BUTTON');
                saveButton.formTarget = this.responseBody.update_url;
                saveButton.id = '';
            }
            if ('delete_url' in this.responseBody) {
                let deleteButton = document.getElementById('NEW_DESTINATION_DELETE_BUTTON');
                deleteButton.formTarget = this.responseBody.delete_url;
                deleteButton.id = '';
            }
            // need to add create-new urls for the add new relaystate / attribute buttons.
        }
    }
}


class RelayStateForm extends Form {
    constructor(eventTarget, id) {
        super(eventTarget);
        this.submittedForm = eventTarget.target.parentElement.parentElement;
    }

    insertNewForm() {
        let container = this.submitButton.parentElement;
        let newForm = this.responseBody['new_form'];
        let formCount = container.children.length;
        let lastForm = container.children[formCount - 2];
        lastForm.insertAdjacentHTML('afterend', newForm);
    }

    getCustomDeleteMessage() {
        let form = this.submittedForm;
        let formData = new FormData(form);
        let url = formData.get('url_pattern');
        let message = `Are you sure you want to delete this item?\n\t
                        URL Pattern = ${url}`
        return message;
    }

    continueProcessing(action) {
        if (action == 'DELETE') {
            let destinationForm = document.getElementById(this.uniqueElementId);
            //let destinationContainer = destinationForm.parentElement;
            destinationForm.remove();
        } else if (action == 'CREATE-NEW') {
            if ('unique_element_id' in this.responseBody) {
                let relayStateForm = document.getElementById('RELAYSTATE_NEW');
                relayStateForm.id = this.responseBody.unique_element_id;
            }
            if ('update_url' in this.responseBody) {
                let saveButton = document.getElementById('NEW_RELAYSTATE_SAVE_BUTTON');
                saveButton.formTarget = this.responseBody.update_url;
                saveButton.id = '';
            }
            if ('delete_url' in this.responseBody) {
                let deleteButton = document.getElementById('NEW_RELAYSTATE_DELETE_BUTTON');
                deleteButton.formTarget = this.responseBody.delete_url;
                deleteButton.id = '';
            }
        }
    }
}

class AttributeForm extends Form {
    constructor(eventTarget, id) {
        super(eventTarget);
        this.submittedForm = eventTarget.target.parentElement.parentElement;
    }

    insertNewForm() {
        let container = this.submitButton.parentElement;
        let newForm = this.responseBody['new_form'];
        let formCount = container.children.length;
        let lastForm = container.children[formCount - 2];
        lastForm.insertAdjacentHTML('afterend', newForm);
    }

    getCustomDeleteMessage() {
        let form = this.submittedForm;
        let formData = new FormData(form);
        let name = formData.get('token_attribute_name');
        let message = `Are you sure you want to delete this item?\n\t
                        Token Attribute Name = ${name}`
        return message;
    }

    continueProcessing(action) {
        if (action == 'DELETE') {
            let form = document.getElementById(this.uniqueElementId);
            form.remove();
        } else if (action == 'CREATE-NEW') {
            if ('unique_element_id' in this.responseBody) {
                let form = document.getElementById('ATTRIBUTE_NEW');
                form.id = this.responseBody.unique_element_id;
            }
            if ('update_url' in this.responseBody) {
                let saveButton = document.getElementById('NEW_ATTRIBUTE_SAVE_BUTTON');
                saveButton.formTarget = this.responseBody.update_url;
                saveButton.id = '';
            }
            if ('delete_url' in this.responseBody) {
                let deleteButton = document.getElementById('NEW_ATTRIBUTE_DELETE_BUTTON');
                deleteButton.formTarget = this.responseBody.delete_url;
                deleteButton.id = '';
            }
        }
    }
}


function submitForm(event) {
    event.preventDefault();
    const UPDATE = 'UPDATE';
    const DELETE = 'DELETE';
    const CREATENEW = 'CREATE-NEW';


    let urlSegments = event.target.formTarget.toUpperCase().split('/');
    let eventTarget = {
        target: event.target,
        url: event.target.formTarget,
        role: urlSegments[2],
        action: urlSegments[3],
        model: urlSegments[4],
        modelId: urlSegments[5],
    };

    let action = eventTarget.action;
    let model = eventTarget.model;

    if (model == 'ENTITY') {
        if (action == UPDATE) {
            let form = new StandardForm(eventTarget);
            form.submitForm(method='POST', action=action);
        }
    } else if (model == 'CERTIFICATE') {
        if (action == CREATENEW) {
            let form = new CertificateForm(eventTarget);
            form.submitForm(method='POST', action=action);
        } else if (action == DELETE) {
            let form = new CertificateForm(eventTarget);
            form.deleteInstance(action);
        }
    } else if (model == 'DESTINATION') {
        if (action == UPDATE) {
            //let form = new StandardForm(eventTarget);
            let form = new DestinationForm(eventTarget);
            form.submitForm(method='POST', action=action);
        } else if (action == CREATENEW) {
            let form = new DestinationForm(eventTarget);
            let method = event.target.formMethod;
            if (method.toUpperCase() == 'GET') {
                let newDestinationForm = form.fetchNewForm();
            } else {
                form.submitForm(method=method, action=action);
            }
        } else if (action == DELETE) {
            let form = new DestinationForm(eventTarget);
            form.deleteInstance(action);
        }
    } else if (model ==  'RELAYSTATE') {
        if (action == UPDATE) {
            let form = new StandardForm(eventTarget);
            form.submitForm(method='POST', action=action);
        } else if (action == CREATENEW) {
            let form = new RelayStateForm(eventTarget);
            let method = event.target.formMethod;
            if (method.toUpperCase() == 'GET') {
                let newForm = form.fetchNewForm();
            } else {
                form.submitForm(method=method, action=action);
            }
        } else if (action == DELETE) {
            let form = new RelayStateForm(eventTarget);
            form.deleteInstance(action);
        }
    } else if (model == 'ATTRIBUTE') {
        if (action == UPDATE) {
            let form = new StandardForm(eventTarget);
            form.submitForm(method='POST', action=action);
        } else if (action == CREATENEW) {
            let form = new AttributeForm(eventTarget);
            let method = event.target.formMethod;
            if (method.toUpperCase() == 'GET') {
                let newForm = form.fetchNewForm();
            } else {
                form.submitForm(method=method, action=action);
            }
        } else if (action == DELETE) {
            let form = new AttributeForm(eventTarget);
            form.deleteInstance(action);
        }
    }
}

function displayCertificateForm(){
    let certificateForm = document.getElementById("certificateForm");
    let addCertificateButton = document.getElementById("addCertificateButton");

    if (certificateForm.hasAttribute('style')) {
        certificateForm.removeAttribute('style');
        addCertificateButton.value = 'Hide Certificate Form'
    } else {
        certificateForm.setAttribute('style', 'display:none')
        addCertificateButton.value = 'Add Certificate'
    }
    toggleUploadMethod();
}

function toggleUploadMethod() {
    let upload_method = document.getElementById("id_upload_method");
    let selectedOption = upload_method.options[upload_method.selectedIndex].value;
    let id_certificate_text = document.getElementById("id_certificate_text").parentElement;
    let id_certificate_file = document.getElementById("id_certificate_file").parentElement;
    if (selectedOption == 'FILE') {
        id_certificate_text.style = "display:none";
        id_certificate_file.style = "";
    } else {
        id_certificate_file.style = "display:none";
        id_certificate_text.style = "";
    }
}
let upload_method = document.getElementById("id_upload_method").parentElement;
upload_method.addEventListener("input", toggleUploadMethod);

function download(data, filename) {
    //var file = new Blob([data], {type: type});
    var file = new Blob([data], {type: 'text/plain'});
    if (window.navigator.msSaveOrOpenBlob) // IE10+
        window.navigator.msSaveOrOpenBlob(file, filename);
    else { // Others
        var a = document.createElement("a"),
                url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename + '.cer';
        document.body.appendChild(a);
        a.click();
        setTimeout(function() {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 0);
    }
}



function updateVisibleSectionIndicators(e) {
    let viewHeight = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
    let viewTop = e.target.scrollTop;
    let viewBottom = viewHeight + viewTop;

    let entityConfig = document.getElementById("entityConfiguration");
    let entityConfigEnd = document.getElementById("entityConfigurationEnd");
    let entityNav = document.getElementById("entityNav");

    let certificateConfig = document.getElementById("certificateConfiguration");
    let certificateConfigEnd = document.getElementById("certificateConfigurationEnd");
    let certificateNav = document.getElementById("certificateNav");

    let destinationConfig = document.getElementById("destinationConfiguration");
    let destinationConfigEnd = document.getElementById("destinationConfigurationEnd");
    let destinationNav = document.getElementById("destinationNav");

    let relayStateConfig = document.getElementById("relayStateConfiguration");
    let relayStateConfigEnd = document.getElementById("relayStateConfigurationEnd");
    let relayStateNav = document.getElementById("relayStateNav");

    let attributeConfig = document.getElementById("attributeConfiguration");
    let attributeConfigEnd = document.getElementById("attributeConfigurationEnd");
    let attributeNav = document.getElementById("attributeNav");

    let configList = [entityConfig, certificateConfig, destinationConfig, relayStateConfig, attributeConfig];
    let configEndList = [entityConfigEnd, certificateConfigEnd, destinationConfigEnd, relayStateConfigEnd, attributeConfigEnd]
    let navList = [entityNav, certificateNav, destinationNav, relayStateNav, attributeNav];

    for (let i = 0; i < configList.length; i++) {
        let temp = isElementInView(viewTop, viewBottom, configList[i], configEndList[i], navList[i]);
        // if (temp) {
        //     break;
        // }
    }

    // let relayStateInView = isElementInView(viewTop, viewBottom, relayStateConfig, relayStateNav);
    // if (relayStateInView) {
    //     console.log('Your RelayState is showingggg!');
    // }

}

function isElementInView(viewTop, viewBottom, element, elementEnd, relatedNavElement) {
    /*
    This needs a few improvements..
    #1 - I need the location for the bottom of each element..
            right now the moment the header hits the top it un-highlights
    #2 - Only highlight an element if
            A: The top and bottom are within view
            B: Or the element is currently taking up over ~half of the viewheight
            This fixes two problems..
                The first is that a nav element is highlighted when only a small part of the element is showing
                The second is that an element that is larger than the viewport (such as relaystates or attributes)
                    would never be highlighted since they would extend past the top and bottom of the screen.

    ALT Solution #2:
        Take the average of the top and bottom of an element (ie the middle)
            and only highlight the element if the average/middle is within the viewport?
    */
    let elementTop = element.offsetTop;
    let elementBottom = elementEnd.offsetTop;
    let elementCenter = ((elementTop + elementBottom) / 2)

    if (elementCenter <= viewBottom && elementCenter >= viewTop) {
        relatedNavElement.style.background = "#C4DBFA";
        return true
    } else {
        relatedNavElement.style.background = "inherit";
        return false;
    }

    // if (elementTop <= viewBottom && elementTop >= viewTop) {
    //     relatedNavElement.style.background = "#C4DBFA";
    //     return true
    // } else {
    //     relatedNavElement.style.background = "inherit";
    //     return false;
    // }
}

function pageScroll(e) {
    // console.log("Page Scroll event.");
    // console.log("ScrollTop:");
    // console.log(e.target.scrollTop);
    // console.log("ScrollBottom:");
    // console.log(e.target.scrollBottom);
    let currentPosition = e.target.scrollTop;

    // need to figure out where the bottom of the window is..


    let entityConfigY = document.getElementById("entityConfiguration").offsetTop;
    let certificateConfigY = document.getElementById("certificateConfiguration").offsetTop;
    let destinationConfigY = document.getElementById("destinationConfiguration").offsetTop;
    let relayStateConfigY = document.getElementById("relayStateConfiguration").offsetTop;
    let attributeConfigY = document.getElementById("attributeConfiguration").offsetTop;

    let relayStateConfigInView = false;
    console.log('relaystate minus current:')
    console.log(relayStateConfigY - currentPosition);

    if (relayStateConfigY - currentPosition > 0) {
        console.log("RelayState is in view!");
    }

    let relayStateRelativePosition = relayStateConfigY - currentPosition;

}