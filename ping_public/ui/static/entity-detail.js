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

        let row = document.getElementById(this.uniqueElementId);
        let message = `Are you sure you want to delete this item?\n\t
                        CN = ${row.children.common_name.innerText}
                        Issue Date = ${row.children.issue_date.innerText}
                        Exp Date = ${row.children.expiration_date.innerText}`
        let userConfirmation = confirm(message);

        if (userConfirmation == true) {
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

//    displayStatusMessage(messageLocation='afterend') {
//        if (this.success) {
//            //let message = this.responseBody.MESSAGE
//            let message = this.responseText
//            let html = `<span id="timedSpan" style="color: green"> ${message} </span`;
//        } else {
//            let html = `<span id="timedSpan" style="color: red"> ${message} </span`;
//        }
//        this.submitButton.insertAdjacentHTML(messageLocation, html);
//        setTimeout( this.removeTimedSpan(), 3000);
//    };
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
            form.submitForm(action);
        }
    } else if (model == 'CERTIFICATE') {
        if (action == CREATENEW) {
            let form = new CertificateForm(eventTarget);
            form.submitForm(action);
        } else if (action == DELETE) {
            let form = new CertificateForm(eventTarget);
            form.deleteInstance(action);
        }
    } else if (model == 'DESTINATION') {
        if (action == UPDATE) {
            let form = new StandardForm(eventTarget);
            form.submitForm(action);
        }
    } else if (model ==  'RELAYSTATE') {
        if (action == UPDATE) {
            let form = new StandardForm(eventTarget);
            form.submitForm(action);
        }
    } else if (model == 'ATTRIBUTE') {
        if (action == UPDATE) {
            let form = new StandardForm(eventTarget);
            form.submitForm(action);
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