"use strict";

document.addEventListener("DOMContentLoaded", function () {
  let deleteForm = document.querySelectorAll("form.delete");

  deleteForm.forEach(form => {
    form.addEventListener("submit", function (event) {
      event.preventDefault();

      if (confirm("Are you sure you want to delete this deck?\nDeletions are permanent!")) {
        form.submit();
      }
    });
  });
});
