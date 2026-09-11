// Main JavaScript for Library Management System

document.addEventListener("DOMContentLoaded", function () {
  // 1. Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // 2. Mobile sidebar toggle
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
  const sidebar = document.getElementById("sidebar");
  const sidebarBackdrop = document.getElementById("sidebarBackdrop");

  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("show");
      if (sidebarBackdrop) {
        sidebarBackdrop.classList.toggle("show");
      }
    });
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener("click", function () {
      if (sidebar) sidebar.classList.remove("show");
      sidebarBackdrop.classList.remove("show");
    });
  }

  // 3. Edit Book Modal population
  const editBookModal = document.getElementById("editBookModal");
  if (editBookModal) {
    editBookModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      if (!button) return;

      const id = button.getAttribute("data-id");
      const isbn = button.getAttribute("data-isbn");
      const title = button.getAttribute("data-title");
      const author = button.getAttribute("data-author");
      const category = button.getAttribute("data-category");
      const totalCopies = button.getAttribute("data-total-copies");
      const publishedYear = button.getAttribute("data-published-year") || "";
      const description = button.getAttribute("data-description") || "";

      const form = document.getElementById("editBookForm");
      if (form) {
        form.action = `/admin/books/edit/${id}`;
        document.getElementById("editBookId").value = id;
        document.getElementById("editBookIsbn").value = isbn;
        document.getElementById("editBookTitle").value = title;
        document.getElementById("editBookAuthor").value = author;
        document.getElementById("editBookCategory").value = category;
        document.getElementById("editBookTotalCopies").value = totalCopies;
        document.getElementById("editBookPublishedYear").value = publishedYear;
        document.getElementById("editBookDescription").value = description;
      }
    });
  }

  // 4. Client-side Instant Filter for Table rows
  const quickSearchInput = document.getElementById("quickTableSearch");
  if (quickSearchInput) {
    quickSearchInput.addEventListener("keyup", function () {
      const filter = quickSearchInput.value.toLowerCase();
      const rows = document.querySelectorAll(".filterable-table tbody tr");

      rows.forEach(function (row) {
        const text = row.innerText.toLowerCase();
        if (text.includes(filter)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });
    });
  }
});

// Helper to quickly fill credentials on the login screen
function fillLogin(username, password) {
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  if (usernameInput && passwordInput) {
    usernameInput.value = username;
    passwordInput.value = password;
  }
}
