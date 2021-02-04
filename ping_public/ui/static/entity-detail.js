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

    async submitForm(method='POST') {
        let formData = new FormData(this.submittedForm);
        let response = await fetch(this.targetUrl,
            {
                method: method,
                body: formData,
                headers: {'X-CSRFToken': csrftoken}
            });
        if (response.ok) {
            this.responseText = await response.text();
            //this.responseBody = response.clone().json();
            //this.responseBody = await response.json();
            this.success = true;
        } else {
            this.response = response;
            this.responseText = await response.text();
            this.responseBody = await response.json();
            this.success = false;
        }
        this.displayStatusMessage();
        this.continueProcessing();
    };

    removeTimedSpan() {
        setTimeout(() => {
            document.getElementById("timedSpan").remove();
        }, 3000);
    };

    displayStatusMessage(messageLocation='afterend') {
        if (this.success) {
            var html = `<span id="timedSpan" style="color: green"> ${this.responseText} </span`;
        } else {
            var html = `<span id="timedSpan" style="color: red"> ${this.responseText} </span`;
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
            form.submitForm();
        }
    } else if (model == 'CERTIFICATE') {
        if (action == CREATENEW) {
            let form = new CertificateForm(eventTarget);
            form.submitForm();
        }
    } else if (model == 'DESTINATION') {
        if (action == UPDATE) {
            let form = new StandardForm(eventTarget);
            form.submitForm();
        }
    } else if (model ==  'RELAYSTATE') {
        if (action == UPDATE) {
            let form = new StandardForm(eventTarget);
            form.submitForm();
        }
    } else if (model == 'ATTRIBUTE') {
        if (action == UPDATE) {
            let form = new StandardForm(eventTarget);
            form.submitForm();
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