async function submitEntityForm(event) {
    event.preventDefault();
    let submittedForm = event.target.parentElement.parentElement;
    let url = submittedForm.action;
    let formData = new FormData(submittedForm);
    let submitButton = event.target;

    let response = await fetch(url,
        {
            method: 'POST',
            body: formData
        });
    if (response.ok) {
        let responseText = await response.text();
        submitButton.insertAdjacentHTML('afterend', `<span id="timedSpan" style="color: green"> ${responseText} </span`);
        setTimeout(() => {
            document.getElementById("timedSpan").remove();
        }, 3000);
        console.log(responseText);
    } else {
        let responseText = await response.text();
        submitButton.insertAdjacentHTML('afterend', `<span id="timedSpan" style="color: red"> ${responseText} </span`);
        setTimeout(() => {
            document.getElementById("timedSpan").remove();
        }, 3000);
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
}

function toggleUploadMethod() {
    console.log('--toggleUploadMethod was triggered---')
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

async function uploadCertificate(event) {
    console.log('----Uploading File----');
    event.preventDefault();
    let button = event.currentTarget;
    let target = button.formTarget;
    let form = button.parentElement;
    let formData = new FormData(form);
    let response = await fetch(target,
        {method: 'POST',
        body: formData}
    );
    if (response.ok) {
        //let responseText = await response.text();
        let responseBody = await response.json();
        //buttonCell.insertAdjacentHTML('afterend', `<span id="timedSpan" style="color: green"> ${responseBody.MESSAGE} </span`);
        button.insertAdjacentHTML('afterend', `<span id="timedSpan" style="color: green"> ${responseBody.MESSAGE} </span`);
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

    console.log('---end----');
}

let upload_method = document.getElementById("id_upload_method").parentElement;
upload_method.addEventListener("click", toggleUploadMethod);