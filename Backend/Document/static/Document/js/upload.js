$(document).ready(function () {
    // --- New elements ---
    const checkTypeRadio = $('input[name="check_type"]'); // Select the radio button group by its name
    const ruleBasedUploadContainer = $('#ruleBasedUploadContainer');
    const requirementFileInput = $('#requirementFileInput');
    const ruleBasedFileInput = $('#ruleBasedFileInput');
    const requirementSelectedFileContainer = $('#requirementSelectedFile');
    const ruleBasedSelectedFileContainer = $('#ruleBasedSelectedFile');
    const requirementFileName = $('#requirementFileName');
    const ruleBasedFileName = $('#ruleBasedFileName');
    const removeRequirementFileBtn = $('#removeRequirementFile');
    const removeRuleBasedFileBtn = $('#removeRuleBasedFile');
    const requirementDropZone = $('#requirementDropZone');
    const ruleBasedDropZone = $('#ruleBasedDropZone');

    // --- Already present elements ---
    const uploadForm = $('#uploadForm');
    const uploadButton = $('#uploadButton');
    const progressBar = $('#progressBar');
    const progressText = $('#progressText');
    const progressBarContainer = $('#progressBarContainer');
    const successAlert = $('#successAlert');
    const errorAlert = $('#errorAlert');
    
    let requirementFile = null;
    let ruleBasedFile = null;

    // Get CSRF token
    const csrftoken = $("input[name=csrfmiddlewaretoken]").val();

    // Event listener for the radio buttons
    checkTypeRadio.on('change', function() {
        const selectedValue = $(this).val(); // Get the value of the selected radio button
        if (selectedValue === 'basic_rule_check' || selectedValue === 'only_rule_check') {
            ruleBasedUploadContainer.slideDown(); // Show the rule-based upload section
        } else {
            ruleBasedUploadContainer.slideUp(); // Hide it for the basic check
            // Also clear the rule-based file if it was selected
            if (ruleBasedFile) {
                ruleBasedFile = null;
                ruleBasedFileInput.val('');
                ruleBasedSelectedFileContainer.addClass('d-none');
                ruleBasedFileName.text('');
            }
        }
    });

    // Helper function to handle file selection logic
    const handleFileSelection = (fileInput, fileNameEl, selectedFileContainer) => {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            fileNameEl.text(file.name);
            selectedFileContainer.removeClass('d-none');
            return file;
        }
        return null;
    };

    // Helper function to handle file removal logic
    const handleFileRemoval = (fileInput, fileNameEl, selectedFileContainer) => {
        fileInput.val('');
        fileNameEl.text('');
        selectedFileContainer.addClass('d-none');
        return null;
    };

    // Handle requirement file selection and removal
    requirementFileInput.on('change', function () {
        requirementFile = handleFileSelection(this, requirementFileName, requirementSelectedFileContainer);
    });
    removeRequirementFileBtn.on('click', function () {
        requirementFile = handleFileRemoval(requirementFileInput, requirementFileName, requirementSelectedFileContainer);
    });

    // Handle rule based file selection and removal
    ruleBasedFileInput.on('change', function () {
        ruleBasedFile = handleFileSelection(this, ruleBasedFileName, ruleBasedSelectedFileContainer);
    });
    removeRuleBasedFileBtn.on('click', function () {
        ruleBasedFile = handleFileRemoval(ruleBasedFileInput, ruleBasedFileName, ruleBasedSelectedFileContainer);
    });

    // Corrected drag and drop handler logic
    const setupDropZone = (dropZone, fileInput, fileNameEl, selectedFileContainer) => {
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
                fileInput[0].files = files;
                if (fileInput[0].id === 'requirementFileInput') {
                    requirementFile = handleFileSelection(fileInput[0], requirementFileName, requirementSelectedFileContainer);
                } else {
                    ruleBasedFile = handleFileSelection(fileInput[0], ruleBasedFileName, ruleBasedSelectedFileContainer);
                }
            }
        });
    };

    setupDropZone(requirementDropZone, requirementFileInput, requirementFileName, requirementSelectedFileContainer);
    setupDropZone(ruleBasedDropZone, ruleBasedFileInput, ruleBasedFileName, ruleBasedSelectedFileContainer);

    // Form Submission Logic (updated for radio buttons)
    uploadForm.on('submit', function (e) {
        e.preventDefault();

        const selectedOption = $('input[name="check_type"]:checked').val();
        const formData = new FormData();
        let validationError = null;

        // Validation based on selected option
        if (selectedOption === 'basic_check') {
            if (!requirementFile) {
                validationError = "⚠️ Please select a requirement document.";
            }
            if (requirementFile) {
                // Corrected: Use the same key 'requirement_document'
                formData.append('requirement_document', requirementFile); 
            }
        } else {
            if (!requirementFile || !ruleBasedFile) {
                validationError = "⚠️ Please upload both the requirement and rule based documents.";
            }
            if (requirementFile) {
                formData.append('requirement_document', requirementFile);
            }
            if (ruleBasedFile) {
                formData.append('rule_based_document', ruleBasedFile);
            }
        }
        
        // Append check type to formData
        formData.append('check_type', selectedOption);

        if (validationError) {
            errorAlert.text(validationError).removeClass('d-none');
            successAlert.addClass('d-none');
            return;
        }

        // --- AJAX logic ---
        progressBarContainer.removeClass('d-none');
        progressBar.css('width', '0%');
        progressText.text('0%');
        successAlert.addClass('d-none');
        errorAlert.addClass('d-none');

        $.ajax({
            url: uploadForm.data('url'),
            type: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            data: formData,
            processData: false,
            contentType: false,
            xhrFields: {
                withCredentials: true
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
                successAlert.text("✅ Documents uploaded & processed successfully!").removeClass('d-none');
                errorAlert.addClass('d-none');
                requirementFile = handleFileRemoval(requirementFileInput, requirementFileName, requirementSelectedFileContainer);
                ruleBasedFile = handleFileRemoval(ruleBasedFileInput, ruleBasedFileName, ruleBasedSelectedFileContainer);
                progressBar.css('width', '100%');
                progressText.text("Done");
            },
            error: function (xhr, status, error) {
                errorAlert.text("❌ Upload failed: " + (xhr.responseText || error)).removeClass('d-none');
                successAlert.addClass('d-none');
                progressText.text("Failed");
            }
        });
    });
});