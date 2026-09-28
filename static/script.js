const phase3Styles = document.createElement("link");
phase3Styles.rel = "stylesheet";
phase3Styles.href = "/static/phase3.css";
phase3Styles.dataset.phase3 = "true";
document.head.appendChild(phase3Styles);

const uploadForm = document.getElementById("upload");
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const selectedFile = document.getElementById("selectedFile");
const uploadButton = document.getElementById("uploadButton");
const uploadProgress = document.getElementById("uploadProgress");
const uploadProgressText = document.getElementById("uploadProgressText");
const uploadProgressPercent = document.getElementById("uploadProgressPercent");
const uploadProgressBar = document.getElementById("uploadProgressBar");

const searchInput = document.getElementById("searchInput");
const categoryFilter = document.getElementById("categoryFilter");
const sortSelect = document.getElementById("sortSelect");
const fileTableBody = document.getElementById("fileTableBody");
const noSearchResults = document.getElementById("noSearchResults");
const clearFilters = document.getElementById("clearFilters");

const fileModal = document.getElementById("fileModal");
const closeModal = document.getElementById("closeModal");
const modalFileName = document.getElementById("modalFileName");
const modalFileType = document.getElementById("modalFileType");
const modalFileSize = document.getElementById("modalFileSize");
const modalFileCategory = document.getElementById("modalFileCategory");
const modalFileModified = document.getElementById("modalFileModified");
const modalDownloadButton = document.getElementById("modalDownloadButton");
const modalPreviewButton = document.getElementById("modalPreviewButton");
const previewPanel = document.getElementById("previewPanel");

const folderForm = document.getElementById("folderForm");
const folderNameInput = document.getElementById("folderNameInput");

let activeModalRow = null;

function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    const value = bytes / Math.pow(1024, index);
    return `${index === 0 ? value.toFixed(0) : value.toFixed(2)} ${units[index]}`;
}

function updateSelectedFile() {
    if (!fileInput || !selectedFile) return;
    const file = fileInput.files?.[0];
    selectedFile.textContent = file ? `${file.name} • ${formatBytes(file.size)}` : "No file selected";
}

if (dropZone && fileInput) {
    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            fileInput.click();
        }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove("dragover");
        });
    });

    dropZone.addEventListener("drop", (event) => {
        const files = event.dataTransfer?.files;
        if (files?.length) {
            fileInput.files = files;
            updateSelectedFile();
        }
    });

    fileInput.addEventListener("change", updateSelectedFile);
}

if (uploadForm && fileInput) {
    const originalButtonLabel = uploadButton?.textContent || "Upload file";

    uploadForm.addEventListener("submit", (event) => {
        const file = fileInput.files?.[0];
        if (!file) return;
        event.preventDefault();

        const maxBytes = Number(uploadForm.dataset.maxBytes || 0);
        if (maxBytes && file.size > maxBytes) {
            selectedFile.textContent = `File is too large. Maximum size is ${formatBytes(maxBytes)}.`;
            return;
        }

        const xhr = new XMLHttpRequest();
        xhr.open("POST", uploadForm.action);

        uploadProgress?.classList.remove("hidden");
        if (uploadProgressBar) uploadProgressBar.style.width = "0%";
        if (uploadProgressPercent) uploadProgressPercent.textContent = "0%";
        if (uploadProgressText) uploadProgressText.textContent = "Uploading…";
        if (uploadButton) {
            uploadButton.disabled = true;
            uploadButton.textContent = "Uploading…";
        }

        xhr.upload.addEventListener("progress", (progressEvent) => {
            if (!progressEvent.lengthComputable) return;
            const percent = Math.min(Math.round((progressEvent.loaded / progressEvent.total) * 100), 100);
            if (uploadProgressBar) uploadProgressBar.style.width = `${percent}%`;
            if (uploadProgressPercent) uploadProgressPercent.textContent = `${percent}%`;
        });

        xhr.addEventListener("load", () => {
            if (xhr.status >= 200 && xhr.status < 400) {
                if (uploadProgressText) uploadProgressText.textContent = "Upload complete";
                if (uploadProgressBar) uploadProgressBar.style.width = "100%";
                if (uploadProgressPercent) uploadProgressPercent.textContent = "100%";
                window.location.assign(xhr.responseURL || window.location.href);
                return;
            }
            if (uploadProgressText) uploadProgressText.textContent = "Upload failed. Please try again.";
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.textContent = originalButtonLabel;
            }
        });

        xhr.addEventListener("error", () => {
            if (uploadProgressText) uploadProgressText.textContent = "Network error. Upload could not be completed.";
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.textContent = originalButtonLabel;
            }
        });

        xhr.send(new FormData(uploadForm));
    });
}

function getRows() {
    return fileTableBody ? [...fileTableBody.querySelectorAll(".file-row")] : [];
}

function compareRows(a, b, mode) {
    const nameA = a.dataset.name.toLowerCase();
    const nameB = b.dataset.name.toLowerCase();
    const sizeA = Number(a.dataset.size);
    const sizeB = Number(b.dataset.size);
    const modifiedA = Number(a.dataset.modified);
    const modifiedB = Number(b.dataset.modified);

    switch (mode) {
        case "oldest": return modifiedA - modifiedB;
        case "name-asc": return nameA.localeCompare(nameB);
        case "name-desc": return nameB.localeCompare(nameA);
        case "size-desc": return sizeB - sizeA;
        case "size-asc": return sizeA - sizeB;
        default: return modifiedB - modifiedA;
    }
}

function applyFileControls() {
    const rows = getRows();
    if (!rows.length) return;
    const query = searchInput?.value.trim().toLowerCase() || "";
    const category = categoryFilter?.value || "all";
    const sortMode = sortSelect?.value || "newest";

    rows.sort((a, b) => compareRows(a, b, sortMode)).forEach((row) => fileTableBody.appendChild(row));
    let visibleCount = 0;
    rows.forEach((row) => {
        const visible = row.dataset.filename.includes(query) && (category === "all" || row.dataset.category === category);
        row.classList.toggle("hidden", !visible);
        if (visible) visibleCount += 1;
    });
    noSearchResults?.classList.toggle("hidden", visibleCount !== 0);
}

[searchInput, categoryFilter, sortSelect].forEach((control) => {
    if (control) control.addEventListener(control === searchInput ? "input" : "change", applyFileControls);
});

clearFilters?.addEventListener("click", () => {
    if (searchInput) searchInput.value = "";
    if (categoryFilter) categoryFilter.value = "all";
    if (sortSelect) sortSelect.value = "newest";
    applyFileControls();
    searchInput?.focus();
});

function clearPreview() {
    if (!previewPanel) return;
    previewPanel.replaceChildren();
    previewPanel.classList.add("hidden");
    if (modalPreviewButton) modalPreviewButton.textContent = "Show preview";
}

function renderPreview(row) {
    if (!previewPanel || row.dataset.previewable !== "true" || !row.dataset.previewUrl) return;
    previewPanel.replaceChildren();

    if (row.dataset.category === "image") {
        const image = document.createElement("img");
        image.src = row.dataset.previewUrl;
        image.alt = `Preview of ${row.dataset.name}`;
        previewPanel.appendChild(image);
    } else {
        const frame = document.createElement("iframe");
        frame.src = row.dataset.previewUrl;
        frame.title = `Preview of ${row.dataset.name}`;
        previewPanel.appendChild(frame);
    }

    previewPanel.classList.remove("hidden");
    if (modalPreviewButton) modalPreviewButton.textContent = "Hide preview";
}

function openFileModal(row, showPreview = false) {
    if (!fileModal || !row) return;
    activeModalRow = row;
    modalFileName.textContent = row.dataset.name;
    modalFileType.textContent = row.dataset.extension.toUpperCase();
    modalFileSize.textContent = row.dataset.sizeLabel;
    modalFileCategory.textContent = row.dataset.category.charAt(0).toUpperCase() + row.dataset.category.slice(1);
    modalFileModified.textContent = row.dataset.modifiedLabel;
    modalDownloadButton.href = row.dataset.downloadUrl;

    const canPreview = row.dataset.previewable === "true";
    modalPreviewButton?.classList.toggle("hidden", !canPreview);
    clearPreview();
    if (showPreview && canPreview) renderPreview(row);

    if (typeof fileModal.showModal === "function") {
        fileModal.showModal();
        document.body.classList.add("modal-open");
    }
}

document.querySelectorAll(".details-trigger").forEach((button) => button.addEventListener("click", () => openFileModal(button.closest(".file-row"))));
document.querySelectorAll(".preview-trigger").forEach((button) => button.addEventListener("click", () => openFileModal(button.closest(".file-row"), true)));

modalPreviewButton?.addEventListener("click", () => {
    if (!activeModalRow || !previewPanel) return;
    previewPanel.classList.contains("hidden") ? renderPreview(activeModalRow) : clearPreview();
});

function closeFileModal() {
    if (fileModal?.open) fileModal.close();
}

closeModal?.addEventListener("click", closeFileModal);
fileModal?.addEventListener("click", (event) => {
    if (event.target === fileModal) closeFileModal();
});
fileModal?.addEventListener("close", () => {
    document.body.classList.remove("modal-open");
    activeModalRow = null;
    clearPreview();
});

document.querySelectorAll("[data-open-folder-form]").forEach((button) => {
    button.addEventListener("click", () => {
        folderForm?.classList.remove("hidden");
        folderNameInput?.focus();
    });
});

document.querySelectorAll("[data-close-folder-form]").forEach((button) => {
    button.addEventListener("click", () => {
        folderForm?.classList.add("hidden");
        if (folderNameInput) folderNameInput.value = "";
    });
});

document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        const message = form.dataset.confirm || "Continue with this action?";
        if (!window.confirm(message)) event.preventDefault();
    });
});
