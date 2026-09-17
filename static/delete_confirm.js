let deleteForm = null;


function showDeleteConfirmation(userName, form) {

    const modal = document.getElementById("deleteModal");

    const userNameText = document.getElementById("deleteUserName");


    userNameText.textContent = userName;

    deleteForm = form;

    modal.style.display = "flex";
}


function closeDeleteConfirmation() {

    const modal = document.getElementById("deleteModal");

    modal.style.display = "none";

    deleteForm = null;
}


function confirmDelete() {

    if (deleteForm) {

        deleteForm.submit();

    }

}