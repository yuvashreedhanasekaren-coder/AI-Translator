let restoreForm = null;

function showRestoreConfirmation(userName, form) {

    const modal = document.getElementById("restoreModal");
    const userNameText = document.getElementById("restoreUserName");

    userNameText.textContent = userName;

    restoreForm = form;

    modal.style.display = "flex";
}


function closeRestoreConfirmation() {

    const modal = document.getElementById("restoreModal");

    modal.style.display = "none";

    restoreForm = null;
}


function confirmRestore() {

    if (restoreForm) {
        restoreForm.submit();
    }
}