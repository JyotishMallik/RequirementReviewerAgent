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

    // ✅ Get CSRF token from hidden input rendered by Django
    const csrftoken = $("input[name=csrfmiddlewaretoken]").val();

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

        // ✅ Send extra metadata so Django can use it
        formData.append('fileName', selectedFile.name);
        formData.append('fileType', selectedFile.type || 'application/octet-stream');
        formData.append('fileSize', selectedFile.size);

        progressBarContainer.removeClass('d-none');
        progressBar.css('width', '0%');
        progressText.text('0%');
        successAlert.addClass('d-none');
        errorAlert.addClass('d-none');

        $.ajax({
            url: uploadForm.data('url'),   // ✅ Use URL from template
            type: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            data: formData,
            processData: false,
            contentType: false,
            xhrFields: {
                withCredentials: true  // ✅ Send session cookie so Django knows the user
            },
            xhr: function () {
                let xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function (evt) {
                    if (evt.lengthComputable) {
                        let percentComplete = Math.round((evt.loaded / evt.total) * 100);
                        progressBar.css('width', percentComplete + '%');
                        progressText.text(percentComplete + '%');

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

                fileInput.val('');
                selectedFile = null;
                selectedFileContainer.addClass('d-none');

                progressBar.css('width', '100%');
                progressText.text("Done");

                // Optionally redirect to files page
                // window.location.href = "/files/";
            },
            error: function (xhr, status, error) {
                errorAlert.text("❌ Upload failed: " + (xhr.responseText || error))
                    .removeClass('d-none');
                successAlert.addClass('d-none');
                progressText.text("Failed");
            }
        });
    });
});