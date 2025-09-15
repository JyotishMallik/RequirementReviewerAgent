$(document).ready(function () {
    const fileInput = $('#fileInput');
    const fileName = $('#fileName');
    const selectedFileContainer = $('#selectedFile');
    const removeFileBtn = $('#removeFile');
    const uploadForm = $('#uploadForm');
    const uploadButton = $('#uploadButton');
    const progressBar = $('#progressBar');
    const progressText = $('#progressText');
    const progressBarContainer = $('#progressBarContainer');
    const successAlert = $('#successAlert');
    const errorAlert = $('#errorAlert');
    const dropZone = $('#dropZone');

    let selectedFile = null;

    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Handle file selection
    fileInput.on('change', function () {
        if (this.files.length > 0) {
            selectedFile = this.files[0];
            fileName.text(selectedFile.name);
            selectedFileContainer.removeClass('d-none');
        }
    });

    // Remove file
    removeFileBtn.on('click', function () {
        fileInput.val('');
        selectedFile = null;
        selectedFileContainer.addClass('d-none');
        fileName.text('');
        progressBarContainer.addClass('d-none');
        progressBar.css('width', '0%');
        progressText.text('0%');
        successAlert.addClass('d-none');
        errorAlert.addClass('d-none');
    });

    // Drag and drop
    dropZone.on('dragover', function (e) {
        e.preventDefault();
        dropZone.addClass('drag-over');
    });

    dropZone.on('dragleave', function () {
        dropZone.removeClass('drag-over');
    });

    dropZone.on('drop', function (e) {
        e.preventDefault();
        dropZone.removeClass('drag-over');

        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            selectedFile = files[0];
            fileInput[0].files = files;
            fileName.text(selectedFile.name);
            selectedFileContainer.removeClass('d-none');
        }
    });

    // Handle form submission
    uploadForm.on('submit', function (e) {
        e.preventDefault();

        if (!selectedFile) {
            errorAlert.text("⚠️ Please select a file before uploading.")
                      .removeClass('d-none');
            return;
        }

        const formData = new FormData();
        formData.append('document', selectedFile);
        formData.append('fileName', selectedFile.name);
        formData.append('fileSize', selectedFile.size);
        formData.append('fileType', selectedFile.type);

        progressBarContainer.removeClass('d-none');
        progressBar.css('width', '0%');
        progressText.text('0%');
        successAlert.addClass('d-none');
        errorAlert.addClass('d-none');

        $.ajax({
            url: '/documents/upload/',
            type: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            data: formData,
            processData: false,
            contentType: false,
            xhr: function () {
                let xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function (evt) {
                    if (evt.lengthComputable) {
                        let percentComplete = Math.round((evt.loaded / evt.total) * 100);
                        progressBar.css('width', percentComplete + '%');
                        progressText.text(percentComplete + '%');

                        // When upload is done, show "Processing…"
                        if (percentComplete === 100) {
                            progressText.text("Processing…");
                        }
                    }
                }, false);
                return xhr;
            },
            success: function (response) {
                successAlert.text("✅ File uploaded & processed successfully!")
                            .removeClass('d-none');
                errorAlert.addClass('d-none');

                // Reset file input & preview for next upload
                fileInput.val('');
                selectedFile = null;
                selectedFileContainer.addClass('d-none');

                // Keep bar full but update label
                progressBar.css('width', '100%');
                progressText.text("Done");
            },
            error: function (xhr, status, error) {
                errorAlert.text("❌ Upload failed: " + error)
                          .removeClass('d-none');
                successAlert.addClass('d-none');
                progressText.text("Failed");
            }
        });
    });
});