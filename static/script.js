const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const selectedFile = document.getElementById("selectedFile");
const searchInput = document.getElementById("searchInput");
const noSearchResults = document.getElementById("noSearchResults");

if (dropZone && fileInput) {
    const updateSelectedFile = () => {
        const file = fileInput.files?.[0];
        selectedFile.textContent = file
            ? `${file.name} • ${(file.size / (1024 * 1024)).toFixed(2)} MB`
            : "No file selected";
    };

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
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateSelectedFile();
        }
    });

    fileInput.addEventListener("change", updateSelectedFile);
}

if (searchInput) {
    searchInput.addEventListener("input", () => {
        const query = searchInput.value.trim().toLowerCase();
        const rows = [...document.querySelectorAll(".file-row")];
        let visibleCount = 0;

        rows.forEach((row) => {
            const isMatch = row.dataset.filename.includes(query);
            row.classList.toggle("hidden", !isMatch);
            if (isMatch) visibleCount += 1;
        });

        if (noSearchResults) {
            noSearchResults.classList.toggle("hidden", visibleCount !== 0 || query === "");
        }
    });
}
