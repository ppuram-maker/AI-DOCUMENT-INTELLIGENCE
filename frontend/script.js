// ==========================================================================
// AI Document Intelligence — Frontend Application Logic
// ==========================================================================

const API_BASE_URL = "";
// ================================
// Authentication
// ================================

let isLoginMode = true;

const authScreen = document.getElementById("authScreen");
const appLayout = document.getElementById("appLayout");

const authTitle = document.getElementById("authTitle");
const authSubtitle = document.getElementById("authSubtitle");
const authUsername = document.getElementById("authUsername");
const authEmail = document.getElementById("authEmail");
authEmail.classList.add("hidden");
const authPassword = document.getElementById("authPassword");
const authBtn = document.getElementById("authBtn");
const authError = document.getElementById("authError");
const authSwitchBtn = document.getElementById("authSwitchBtn");
const logoutBtn = document.getElementById("logoutBtn");
function handleUnauthorized() {
  localStorage.removeItem("access_token");

  appLayout.classList.add("hidden");
  authScreen.classList.remove("hidden");

  authUsername.value = "";
  authEmail.value = "";
  authPassword.value = "";

  clearAuthError();
  showAuthError("Your session has expired. Please login again.");
}

function showAuthError(message) {
  authError.textContent = message;
  authError.classList.remove("hidden");
}

function clearAuthError() {
  authError.textContent = "";
  authError.classList.add("hidden");
}

authSwitchBtn.addEventListener("click", () => {
  isLoginMode = !isLoginMode;

  clearAuthError();

  if (isLoginMode) {
    authEmail.classList.add("hidden");
    authTitle.textContent = "Login";
    authSubtitle.textContent = "Login to access your documents.";
    authBtn.textContent = "Login";
    authSwitchBtn.textContent = "Register";
    authSwitchBtn.parentElement.firstChild.textContent =
      "Don't have an account? ";
  } else {
    authEmail.classList.remove("hidden");
    authTitle.textContent = "Register";
    authSubtitle.textContent = "Create an account to get started.";
    authBtn.textContent = "Register";
    authSwitchBtn.textContent = "Login";
    authSwitchBtn.parentElement.firstChild.textContent =
      "Already have an account? ";
  }
});

authBtn.addEventListener("click", async () => {
  
  clearAuthError();

  const username = authUsername.value.trim();
  const password = authPassword.value;

  if (!username || !password) {
  showAuthError("Please enter username and password.");
  return;
}

if (!isLoginMode && !authEmail.value.trim()) {
  showAuthError("Please enter your email address.");
  return;
}

  try {
    if (isLoginMode) {
      // Login
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: username,
          password: password
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed.");
      }

      localStorage.setItem("access_token", data.access_token);

      authScreen.classList.add("hidden");
      appLayout.classList.remove("hidden");

      fetchDocuments();

    } else {
      // Register
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: username,
          email: authEmail.value.trim(),
          password: password
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Registration failed.");
      }

      showToast("Registration successful! Please login.", "success");
      isLoginMode = true;
      authTitle.textContent = "Login";
      authSubtitle.textContent = "Login to access your documents.";
      authBtn.textContent = "Login";
      authSwitchBtn.textContent = "Register";
      authSwitchBtn.parentElement.firstChild.textContent =
        "Don't have an account? ";

      authPassword.value = "";
    }

  } catch (error) {
    showAuthError(error.message);
  }
  });
  logoutBtn.addEventListener("click", () => {
    if (!confirm("Are you sure you want to logout?")) {
      return;
    }
  localStorage.removeItem("access_token");

  appLayout.classList.add("hidden");
  authScreen.classList.remove("hidden");

  authUsername.value = "";
  authEmail.value = "";
  authPassword.value = "";

  clearAuthError();
});  

// DOM Elements: Upload & Actions
const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const browseBtn = document.getElementById("browseBtn");
const fileInfo = document.getElementById("fileInfo");
const selectedFileName = document.getElementById("selectedFileName");
const selectedFileSize = document.getElementById("selectedFileSize");
const removeFileBtn = document.getElementById("removeFileBtn");
const generateBtn = document.getElementById("generateBtn");
const loadingIndicator = document.getElementById("loadingIndicator");
const uploadError = document.getElementById("uploadError");

// DOM Elements: Summary Panel
const summaryResult = document.getElementById("summaryResult");
const resultFilename = document.getElementById("resultFilename");
const summaryText = document.getElementById("summaryText");

// DOM Elements: History & Notifications
const documentsList = document.getElementById("documentsList");
const emptyHistory = document.getElementById("emptyHistory");
const refreshBtn = document.getElementById("refreshBtn");
const toast = document.getElementById("toast");

// DOM Elements: Document Details Modal
const viewModal = document.getElementById("viewModal");
const modalOverlay = document.getElementById("modalOverlay");
const closeModalBtn = document.getElementById("closeModalBtn");
const modalCloseActionBtn = document.getElementById("modalCloseActionBtn");
const modalFilename = document.getElementById("modalFilename");
const modalDate = document.getElementById("modalDate");
const modalSummary = document.getElementById("modalSummary");
const modalExtractedText = document.getElementById("modalExtractedText");

// Selected file state
let currentFile = null;

// ==========================================================================
// 1. Reusable Toast Notification System
// ==========================================================================
let toastTimer = null;

function showToast(message, type = "success") {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.className = `toast-notification toast-${type}`;
  toast.classList.remove("hidden");

  toastTimer = setTimeout(() => {
    toast.classList.add("hidden");
  }, 3500);
}

// ==========================================================================
// 2. Formatters & Helpers
// ==========================================================================
function formatBytes(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function formatDate(dateString) {
  if (!dateString) return "Recently";
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateString;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function clearErrors() {
  uploadError.classList.add("hidden");
  uploadError.textContent = "";
}

function showError(message) {
  uploadError.textContent = message;
  uploadError.classList.remove("hidden");
}

// ==========================================================================
// 3. File Selection & Drag-and-Drop Handling
// ==========================================================================
function setSelectedFile(file) {
  if (!file) return;

  if (file.size > 50 * 1024 * 1024) {

    showError("File size must be less than 50MB.");
    return;
}

  // Validate PDF extension
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showError("Please select a valid PDF file (.pdf).");
    return;
  }

  clearErrors();
  currentFile = file;
  selectedFileName.textContent = file.name;
  selectedFileSize.textContent = formatBytes(file.size);

  fileInfo.classList.remove("hidden");
  dropZone.classList.add("hidden");
}

function resetFileInput() {
  currentFile = null;
  fileInput.value = "";
  fileInfo.classList.add("hidden");
  dropZone.classList.remove("hidden");
  clearErrors();
}

// Browse button triggers hidden input
browseBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  fileInput.click();
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files[0]) {
    setSelectedFile(e.target.files[0]);
  }
});

removeFileBtn.addEventListener("click", resetFileInput);

// Drag-and-drop events
["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
  });
});

dropZone.addEventListener("drop", (e) => {
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    setSelectedFile(e.dataTransfer.files[0]);
  }
});

// ==========================================================================
// 4. Summarize Document (POST /summarize)
// ==========================================================================
generateBtn.addEventListener("click", async () => {
  clearErrors();

  if (!currentFile) {
    showError("Please select a PDF document first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", currentFile);

  // Set loading state
  generateBtn.disabled = true;
  loadingIndicator.classList.remove("hidden");
  summaryResult.classList.add("hidden");

  try {
    const response = await fetch(`${API_BASE_URL}/summarize`, {

      method: "POST",
      headers: {


        "Authorization": `Bearer ${localStorage.getItem("access_token")}`

        },

        body: formData,

        });

    if (response.status === 401) {

      handleUnauthorized();
      return;
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API error ${response.status}`);
    }

    const data = await response.json();

    // Render AI summary card
    resultFilename.textContent = data.filename || currentFile.name;
    summaryText.textContent = data.summary || "No summary generated.";
    summaryResult.classList.remove("hidden");

    showToast("Summary generated successfully.");

    // Automatically update history
    fetchDocuments();
  } catch (err) {
    console.error("Summarization error:", err);
    showError(err.message || "Unable to generate summary. Please try again.");
    showToast(err.message || "Unable to generate summary. Please try again.", "error");

  } finally {
    generateBtn.disabled = false;
    loadingIndicator.classList.add("hidden");
  }
});

// ==========================================================================
// 5. Document History (GET /documents)
// ==========================================================================
async function fetchDocuments() {
  try {
    const response = await fetch(`${API_BASE_URL}/documents`, {

    headers: {

      "Authorization": `Bearer ${localStorage.getItem("access_token")}`
      }
      });
      
    if (!response.ok) {
      if (response.status === 401) {
        handleUnauthorized();
        return;
      }
      throw new Error(`History fetch error ${response.status}`);
    }

    const documents = await response.json();
    renderDocuments(documents);
  } catch (err) {
    console.error("History fetch error:", err);
    showToast("Unable to load document history. Please try again.", "error");
  }
}

function renderDocuments(documents) {
  documentsList.innerHTML = "";

  if (!documents || documents.length === 0) {
    emptyHistory.classList.remove("hidden");
    return;
  }

  emptyHistory.classList.add("hidden");

  documents.forEach((doc) => {
    const item = document.createElement("div");
    item.className = "document-item";
    item.id = `doc-${doc.id}`;

    item.innerHTML = `
      <div class="doc-top-bar">
        <div class="doc-title-group">
          <span class="doc-file-icon">📄</span>
          <h3 class="doc-name" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</h3>
        </div>
        <span class="doc-date">Created: ${formatDate(doc.created_at)}</span>
      </div>
      <p class="doc-summary-preview">${escapeHtml(doc.summary || "No summary available.")}</p>
      <div class="doc-actions">
        <button class="btn btn-secondary btn-sm" onclick="viewDocument(${doc.id})">View</button>
        <button class="btn btn-danger-outline btn-sm" onclick="deleteDocumentItem(${doc.id})">Delete</button>
      </div>
    `;

    documentsList.appendChild(item);
  });
}

refreshBtn.addEventListener("click", fetchDocuments);

// ==========================================================================
// 6. View Document Details (GET /documents/{id})
// ==========================================================================
async function viewDocument(documentId) {
  try {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("access_token")}`
      }
    });
    if (!response.ok) {
      throw new Error(`Document fetch error ${response.status}`);
    }

    const doc = await response.json();

    // Populate modal fields
    modalFilename.textContent = doc.filename;
    modalDate.textContent = `Created: ${formatDate(doc.created_at)}`;
    modalSummary.textContent = doc.summary || "No summary recorded.";
    modalExtractedText.textContent = doc.extracted_text || "No extracted text recorded.";

    // Open modal
    viewModal.classList.remove("hidden");
  } catch (err) {
    console.error("View document error:", err);
    showToast("Unable to load document details. Please try again.", "error");
  }
}

function closeModal() {
  viewModal.classList.add("hidden");
}

closeModalBtn.addEventListener("click", closeModal);
modalCloseActionBtn.addEventListener("click", closeModal);
modalOverlay.addEventListener("click", closeModal);

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !viewModal.classList.contains("hidden")) {
    closeModal();
  }
});

// ==========================================================================
// 7. Delete Document (DELETE /documents/{id})
// ==========================================================================
async function deleteDocumentItem(documentId) {
  const confirmed = confirm("Are you sure you want to delete this document?");
  if (!confirmed) return;

  try {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {

      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("access_token")}`
        }
        });

    if (!response.ok) {
      throw new Error(`Delete error ${response.status}`);
    }

    // Immediately remove the card from the UI
    const card = document.getElementById(`doc-${documentId}`);
    if (card) {
      card.remove();
    }

    // If history is now empty, reveal the empty state card
    if (documentsList.children.length === 0) {
      emptyHistory.classList.remove("hidden");
    }

    showToast("Document deleted successfully.");
  } catch (err) {
    console.error("Delete document error:", err);
    showToast("Unable to delete document. Please try again.", "error");
  }
}

// Expose handlers globally for inline HTML onclick attributes
window.viewDocument = viewDocument;
window.deleteDocumentItem = deleteDocumentItem;

// Initial fetch on application load
document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");

  if (token) {
    authScreen.classList.add("hidden");
    appLayout.classList.remove("hidden");
    fetchDocuments();
  }
});
