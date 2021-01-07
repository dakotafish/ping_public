

function editEntity() {
    let entityFieldSet = document.getElementById('entityFieldSet');
    let editEntityButton = document.getElementById('editEntityButton');
    if (entityFieldSet.hasAttribute('disabled')) {
        entityFieldSet.removeAttribute('disabled');
        editEntityButton.value = 'Cancel'
    } else {
        entityFieldSet.setAttribute('disabled', 'disabled')
        editEntityButton.value = 'Edit Entity'
    }
}
