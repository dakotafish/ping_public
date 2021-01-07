
console.log('working...');

function submitForm(event){
    event.preventDefault();
    let submittedForm = event.target;
    let url = submittedForm.action;
    let formData = new FormData(submittedForm);
    fetch(url, {
    method: 'POST',
    body: formData
    })
    .then(response => {
        console.log('..Received the response...')
        console.log(response.status)
        console.log(response)
        console.log(response.text())
        console.log('----')
    })
    .then(result => {
        console.log('Success: ', result);
    });
}


function testing(event) {
    console.log("---");
    console.log(event)
    console.log(event.target);
    console.log(event.target.innerHTML);
    console.log('----');
    console.log(event.srcElement);
    console.log(event.srcElement.innerHTML);
    console.log(event.attributes);
    console.log(event.timeStamp);
    console.log("---");
    //event.preventDefault();
}

let form = document.entityForm;
form.addEventListener("submit", submitForm);
//function Data(event, el) {
//    console.log("---");
//    console.log(event);
//    console.log(el);
//    event.preventDefault();
//    console.log("---")
//};
//
//let form = document.entityForm;
//form.addEventListener("submit", Data(event, this));




//console.log('test');
//let form = document.entityForm;
//form.addEventListener("submit", event => {
//    console.log("It worked.");
//    console.log(this.innerHTML);
//    event.preventDefault();
//}
//);
function editEntity() {
    document.getElementById('entityFieldSet').removeAttribute('disabled');
}
//
//
//function test(event, this) {
//    event.preventDefault();
//    console.log("---");
//    console.log(this);
//    console.log(this.innerHTML);
//    console.log(event);
//    console.log('---');
//}
//form.addEventListener("submit", test(event, this));


//I think I just need to add event listeners on all of the forms? Also need to know which form is being submitted when there are multiple.. Something with "this" ? idk