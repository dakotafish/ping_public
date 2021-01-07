
let certificateForm = document.getElementById("certificateForm");

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

function toggleUploadMethod(event) {
    let selectedOption = upload_method.options[upload_method.selectedIndex].value;
    let id_certificate_text = document.getElementById("id_certificate_text");
    let id_certificate_file = document.getElementById("id_certificate_file");
    if (selectedOption == 'FILE') {
        id_certificate_text.style = "display:none"
    } else {
        id_certificate_file.style = "display:none"
    }
}

let upload_method = document.getElementById("id_upload_method");
upload_method.addEventListener("click", toggleUploadMethod(event));
// well that doesn't work


const fileSelect = document.getElementById("fileSelect"), fileElem = document.getElementById("fileElem");
const csrfTokenValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken'))
    .split('=')[1];

fileSelect.addEventListener("click", function (e) {
  if (fileElem) {
    fileElem.click();
  }
}, false);

const selectedFile = document.getElementById('fileElem').files[0];


const upload = (file) => {
  fetch('http://127.0.0.1:8000/ui/test', { // Your POST endpoint
    method: 'POST',
    headers: {
      // Content-Type may need to be completely **omitted**
      // or you may need something
      //"Content-Type": "You will perhaps need to define a content-type here"
      "X-CSRFToken": csrfTokenValue
    },
    body: file // This is your file object
  }).then(
    response => response.text() // if the response is a JSON object
  ).then(
    success => console.log(success) // Handle the success response object
  ).catch(
    error => console.log(error) // Handle the error response object
  );
};