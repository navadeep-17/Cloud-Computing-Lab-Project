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
        if (files?.length > 0) {
            fileInput.files = files;
            updateSelectedFile();
        }
    });

    fileInput.addEventListener("change", updateSelectedFile);
}

if (uploadForm && fileInput) {
    uploadForm.addEventListener("submit", (event) => {
        const file = fileInput.files?.[0];
        if (!file) return;

        event.preventDefault();

        const maxBytes = Number(uploadForm.dataset.maxBytes || 0);
        if (maxBytes && file.size > maxBytes) {
            selectedFile.textContent = `File is too large. Maximum size is ${formatBytes(maxBytes)}.`;
            return;
        }

        const formData = new FormData(uploadForm);
        const xhr = new XMLHttpRequest();
        xhr.open("POST", uploadForm.action);

        if (uploadProgress && uploadProgressBar && uploadProgressPercent && uploadProgressText) {
            uploadProgress.classList.remove("hidden");
            uploadProgressBar.style.width = "0%";
            uploadProgressPercent.textContent = "0%";
            uploadProgressText.textContent = "Uploading…";
        }

        if (uploadButton) {
            uploadButton.disabled = true;
            uploadButton.textContent = "Uploading…";
        }

        xhr.upload.addEventListener("progress", (progressEvent) => {
            if (!progressEvent.lengthComputable || !uploadProgressBar || !uploadProgressPercent) return;
            const percent = Math.min(Math.round((progressEvent.loaded / progressEvent.total) * 100), 100);
            uploadProgressBar.style.width = `${percent}%`;
            uploadProgressPercent.textContent = `${percent}%`;
        });

        xhr.addEventListener("load", () => {
            if (xhr.status >= 200 && xhr.status < 400) {
                if (uploadProgressText) uploadProgressText.textContent = "Upload complete";
                if (uploadProgressBar) uploadProgressBar.style.width = "100%";
                if (uploadProgressPercent) uploadProgressPercent.textContent = "100%";
                window.location.assign(xhr.responseURL || window.location.pathname);
                return;
            }

            if (uploadProgressText) uploadProgressText.textContent = "Upload failed. Please try again.";
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.textContent = "Upload to CloudVault";
            }
        });

        xhr.addEventListener("error", () => {
            if (uploadProgressText) uploadProgressText.textContent = "Network error. Upload could not be completed.";
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.textContent = "Upload to CloudVault";
            }
        });

        xhr.send(formData);
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
        case "oldest":
            return modifiedA - modifiedB;
        case "name-asc":
            return nameA.localeCompare(nameB);
        case "name-desc":
            return nameB.localeCompare(nameA);
        case "size-desc":
            return sizeB - sizeA;
        case "size-asc":
            return sizeA - sizeB;
        case "newest":
        default:
            return modifiedB - modifiedA;
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
        const matchesSearch = row.dataset.filename.includes(query);
        const matchesCategory = category === "all" || row.dataset.category === category;
        const isVisible = matchesSearch && matchesCategory;
        row.classList.toggle("hidden", !isVisible);
        if (isVisible) visibleCount += 1;
    });

    if (noSearchResults) {
        noSearchResults.classList.toggle("hidden", visibleCount !== 0);
    }
}

[searchInput, categoryFilter, sortSelect].forEach((control) => {
    if (!control) return;
    control.addEventListener(control === searchInput ? "input" : "change", applyFileControls);
});

if (clearFilters) {
    clearFilters.addEventListener("click", () => {
        if (searchInput) searchInput.value = "";
        if (categoryFilter) categoryFilter.value = "all";
        if (sortSelect) sortSelect.value = "newest";
        applyFileControls();
        searchInput?.focus();
    });
}

function clearPreview() {
    if (!previewPanel) return;
    previewPanel.replaceChildren();
    previewPanel.classList.add("hidden");
    if (modalPreviewButton) modalPreviewButton.textContent = "Show preview";
}

function renderPreview(row) {
    if (!previewPanel || row.dataset.previewable !== "true" || !row.dataset.previewUrl) return;

    previewPanel.replaceChildren();
    const category = row.dataset.category;

    if (category === "image") {
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

document.querySelectorAll(".details-trigger").forEach((button) => {
    button.addEventListener("click", () => openFileModal(button.closest(".file-row"), false));
});

document.querySelectorAll(".preview-trigger").forEach((button) => {
    button.addEventListener("click", () => openFileModal(button.closest(".file-row"), true));
});

if (modalPreviewButton) {
    modalPreviewButton.addEventListener("click", () => {
        if (!activeModalRow || !previewPanel) return;
        if (previewPanel.classList.contains("hidden")) {
            renderPreview(activeModalRow);
        } else {
            clearPreview();
        }
    });
}

function closeFileModal() {
    if (!fileModal?.open) return;
    fileModal.close();
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
