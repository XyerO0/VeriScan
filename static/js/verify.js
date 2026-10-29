// =========================================================
// VeriScan Industrial Forensic Console Engine
// High-Precision Security Terminal Script (Zero Emojis / SVG Icons)
// =========================================================

document.addEventListener("DOMContentLoaded", function () {
  const docType = document.getElementById("documentType");
  const docLabel = document.getElementById("documentLabel");
  const docInput = document.getElementById("document");
  const nameInput = document.getElementById("name");

  const fileInput = document.getElementById("documentFile");
  const dropzone = document.getElementById("dropzone");
  const filePreview = document.getElementById("filePreview");
  const previewImg = document.getElementById("previewImg");
  const previewName = document.getElementById("previewName");
  const previewSize = document.getElementById("previewSize");
  const removeFileBtn = document.getElementById("removeFileBtn");

  const form = document.getElementById("verifyForm");
  const submitBtn = document.getElementById("submitBtn");
  const errorDiv = document.getElementById("errorMessage");
  const loadingOverlay = document.getElementById("loadingOverlay");
  const resultPlaceholder = document.getElementById("resultPlaceholder");
  const resultContent = document.getElementById("resultContent");
  const telemetryStatus = document.getElementById("telemetryStatus");

  // Demo Fixtures
  const presetPan = document.getElementById("presetPan");
  const presetAadhaar = document.getElementById("presetAadhaar");
  const presetVisa = document.getElementById("presetVisa");

  // SVG Icon Templates (Vector Only)
  const iconCheck = `<svg class="icon icon-sm" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>`;
  const iconCross = `<svg class="icon icon-sm" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
  const iconAlert = `<svg class="icon icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
  const iconShieldCheck = `<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>`;
  const iconShieldAlert = `<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;

  // 1. Dynamic label & placeholder updates
  function updateDocumentPlaceholders(type) {
    if (!docLabel || !docInput) return;
    const labelSpan = docLabel.querySelector("span:first-child");

    if (type === "pan") {
      if (labelSpan) labelSpan.textContent = "PAN NUMBER (ITD 10-CHAR)";
      docInput.placeholder = "e.g. ABCDE1234F (10 characters)";
    } else if (type === "aadhaar") {
      if (labelSpan) labelSpan.textContent = "AADHAAR NUMBER (UIDAI 12-DIGIT)";
      docInput.placeholder = "e.g. 9876 5432 1098 (12 digits)";
    } else if (type === "visa") {
      if (labelSpan) labelSpan.textContent = "VISA DOCUMENT IDENTIFIER";
      docInput.placeholder = "e.g. V9876543";
    } else {
      if (labelSpan) labelSpan.textContent = "DOCUMENT IDENTIFIER #";
      docInput.placeholder = "Enter alphanumeric identifier";
    }
  }

  if (docType) {
    docType.addEventListener("change", function () {
      updateDocumentPlaceholders(this.value);
    });
  }

  // 2. Demo Presets for Quick Evaluation
  if (presetPan) {
    presetPan.addEventListener("click", () => {
      docType.value = "pan";
      updateDocumentPlaceholders("pan");
      nameInput.value = "Rahul Kumar";
      docInput.value = "ABCDE1234F";
    });
  }

  if (presetAadhaar) {
    presetAadhaar.addEventListener("click", () => {
      docType.value = "aadhaar";
      updateDocumentPlaceholders("aadhaar");
      nameInput.value = "Ananya Sharma";
      docInput.value = "2173 1671 9291";
    });
  }

  if (presetVisa) {
    presetVisa.addEventListener("click", () => {
      docType.value = "visa";
      updateDocumentPlaceholders("visa");
      nameInput.value = "John Doe";
      docInput.value = "V9876543";
    });
  }

  // 3. Drag and Drop + File Preview
  function handleSelectedFile(file) {
    if (!file) return;

    if (!file.type.match("image.*")) {
      showError("Unsupported format. Only JPG, JPEG, and PNG images are permitted.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      showError("Payload size exceeded. Artifact exceeds 5 MB limit.");
      return;
    }

    if (errorDiv) errorDiv.classList.add("hidden");

    // Show preview info
    if (previewName) previewName.textContent = file.name;
    const sizeKB = (file.size / 1024).toFixed(1);
    if (previewSize) {
      previewSize.textContent = sizeKB > 1024 ? `${(sizeKB / 1024).toFixed(2)} MB` : `${sizeKB} KB`;
    }

    // Read thumbnail
    const reader = new FileReader();
    reader.onload = function (e) {
      if (previewImg) previewImg.src = e.target.result;
      if (filePreview) filePreview.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
  }

  if (fileInput) {
    fileInput.addEventListener("change", function () {
      if (this.files && this.files[0]) {
        handleSelectedFile(this.files[0]);
      }
    });
  }

  if (dropzone) {
    ["dragenter", "dragover"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        fileInput.files = files;
        handleSelectedFile(files[0]);
      }
    });
  }

  if (removeFileBtn) {
    removeFileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (fileInput) fileInput.value = "";
      if (filePreview) filePreview.classList.add("hidden");
      if (previewImg) previewImg.src = "";
    });
  }

  // 4. Form Submission Handling
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (errorDiv) {
        errorDiv.classList.add("hidden");
        errorDiv.textContent = "";
      }

      const formData = new FormData(form);
      const selectedDocType = formData.get("documentType");
      const enteredName = formData.get("name")?.trim();
      const enteredDoc = formData.get("document")?.trim();
      const selectedFile = fileInput.files ? fileInput.files[0] : null;

      if (!selectedDocType) {
        showError("Document classification standard must be selected.");
        return;
      }
      if (!enteredName) {
        showError("Claimed full name is required for fuzzy verification.");
        return;
      }
      if (!enteredDoc) {
        showError("Document identifier number is required.");
        return;
      }
      if (!selectedFile || selectedFile.size === 0) {
        showError("Document image artifact must be provided.");
        return;
      }

      if (loadingOverlay) loadingOverlay.classList.remove("hidden");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const response = await fetch("/api/verify", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
          throw new Error(data.error || "Forensic screening pipeline returned an error.");
        }

        displayResults(data);
      } catch (err) {
        showError(err.message || "An unexpected error occurred during screening.");
        if (resultContent) resultContent.classList.add("hidden");
        if (resultPlaceholder) resultPlaceholder.classList.remove("hidden");
        if (telemetryStatus) telemetryStatus.textContent = "PIPELINE_ERROR // 500";
      } finally {
        if (loadingOverlay) loadingOverlay.classList.add("hidden");
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  function showError(msg) {
    if (!errorDiv) return;
    errorDiv.innerHTML = `${iconAlert} <span>${msg}</span>`;
    errorDiv.classList.remove("hidden");
  }

  // 5. Display Comprehensive Results in Console
  function displayResults(data) {
    if (resultPlaceholder) resultPlaceholder.classList.add("hidden");
    if (resultContent) resultContent.classList.remove("hidden");
    if (telemetryStatus) telemetryStatus.textContent = "ANALYSIS_COMPLETE // 200 OK";

    // Overall Risk
    const finalRisk = data.final_risk || data.risk || {};
    const riskLevel = finalRisk.level || "Unknown";
    const riskScore = finalRisk.score ?? 0;

    const riskLevelEl = document.getElementById("riskLevel");
    if (riskLevelEl) {
      riskLevelEl.textContent = riskLevel;
      riskLevelEl.className = "risk-tag " + getRiskTagClass(riskLevel);
    }

    const riskScoreEl = document.getElementById("riskScore");
    if (riskScoreEl) {
      riskScoreEl.textContent = riskScore;
    }

    // Telemetry Gauge
    const meterFill = document.getElementById("riskMeterFill");
    if (meterFill) {
      meterFill.style.width = `${Math.min(100, Math.max(0, riskScore))}%`;
      meterFill.className = "gauge-bar " + getGaugeBarClass(riskLevel);
    }

    // Operational Directive (Recommended Next Step)
    const nextStepCard = document.getElementById("nextStepCard");
    const nextStepEl = document.getElementById("nextStepText");
    const nextStep = data.recommended_next_step || finalRisk.recommended_next_step || "Standard human inspection recommended.";
    if (nextStepEl) {
      nextStepEl.textContent = nextStep;
      if (nextStepCard) {
        nextStepCard.className = "directive-box " + getDirectiveClass(riskLevel);
      }
    }

    // Forensic Screening Narrative Explanation
    const explanationEl = document.getElementById("explanationText");
    const explanation = data.explanation || finalRisk.explanation || "Screening completed.";
    if (explanationEl) {
      explanationEl.textContent = explanation;
    }

    // Identity Section
    const identity = data.identity || {};
    const enteredNameEl = document.getElementById("enteredNameDisplay");
    const detectedNameEl = document.getElementById("detectedNameDisplay");
    const nameStatusBadgeEl = document.getElementById("nameStatusBadge");

    if (enteredNameEl) {
      enteredNameEl.textContent = identity.entered_name || (nameInput ? nameInput.value : "--");
    }

    if (detectedNameEl) {
      detectedNameEl.textContent = identity.detected_name || "Not Detected in OCR";
    }

    if (nameStatusBadgeEl) {
      const sim = identity.name_similarity ?? 0;
      const statusText = identity.name_status || (sim >= 85 ? "Match" : (sim < 50 ? "Severe Mismatch" : "Discrepancy"));

      if (sim >= 85) {
        nameStatusBadgeEl.innerHTML = `${iconCheck} ${statusText} (${sim}%)`;
        nameStatusBadgeEl.className = "badge-state state-ok";
      } else if (sim < 50) {
        nameStatusBadgeEl.innerHTML = `${iconShieldAlert} ${statusText} (${sim}%)`;
        nameStatusBadgeEl.className = "badge-state state-bad";
      } else {
        nameStatusBadgeEl.innerHTML = `${iconAlert} ${statusText} (${sim}%)`;
        nameStatusBadgeEl.className = "badge-state state-neutral";
      }
    }

    // Document Rule Check
    const doc = data.document || {};
    const enteredNumberEl = document.getElementById("enteredNumber");
    const detectedNumberEl = document.getElementById("detectedNumber");
    if (enteredNumberEl) enteredNumberEl.textContent = doc.entered_number || "--";
    if (detectedNumberEl) detectedNumberEl.textContent = doc.detected_number || "Not detected";

    const matchEl = document.getElementById("numberMatch");
    if (matchEl) {
      if (doc.number_match === true) {
        matchEl.innerHTML = `${iconCheck} Match`;
        matchEl.className = "badge-state state-ok";
      } else if (doc.number_match === false) {
        matchEl.innerHTML = `${iconCross} Mismatch`;
        matchEl.className = "badge-state state-bad";
      } else {
        matchEl.innerHTML = `${iconAlert} Unknown`;
        matchEl.className = "badge-state state-neutral";
      }
    }

    const formatEl = document.getElementById("formatValid");
    if (formatEl) {
      if (doc.format_valid === true) {
        formatEl.innerHTML = `${iconCheck} Valid Format`;
        formatEl.className = "badge-state state-ok";
      } else if (doc.format_valid === false) {
        formatEl.innerHTML = `${iconCross} Invalid Format`;
        formatEl.className = "badge-state state-bad";
      } else {
        formatEl.innerHTML = `${iconAlert} Unknown`;
        formatEl.className = "badge-state state-neutral";
      }
    }

    const checksumEl = document.getElementById("checksumValid");
    if (checksumEl) {
      if (doc.checksum_valid === false) {
        checksumEl.innerHTML = `${iconCross} Checksum Failed`;
        checksumEl.className = "badge-state state-bad";
      } else {
        checksumEl.innerHTML = `${iconCheck} Verified / Standard`;
        checksumEl.className = "badge-state state-ok";
      }
    }

    const authorityEl = document.getElementById("authorityValid");
    if (authorityEl) {
      if (doc.authority_valid === false) {
        authorityEl.innerHTML = `${iconCross} Missing Headers`;
        authorityEl.className = "badge-state state-bad";
      } else {
        authorityEl.innerHTML = `${iconCheck} Headers Verified`;
        authorityEl.className = "badge-state state-ok";
      }
    }

    // Algorithmic Image Forensics (OpenCV)
    const forensics = data.forensic_analysis || {};
    const forensicStatusEl = document.getElementById("forensicStatus");
    const forensicRiskScoreEl = document.getElementById("forensicRiskScore");
    const forensicConfidenceEl = document.getElementById("forensicConfidence");
    const metadataSoftwareEl = document.getElementById("metadataSoftware");
    const forensicIndicatorsEl = document.getElementById("forensicIndicators");

    if (forensicStatusEl) {
      if (forensics.suspicious) {
        forensicStatusEl.innerHTML = `${iconShieldAlert} Anomaly Detected`;
        forensicStatusEl.className = "badge-state state-bad";
      } else {
        forensicStatusEl.innerHTML = `${iconShieldCheck} Normal / Clean`;
        forensicStatusEl.className = "badge-state state-ok";
      }
    }

    if (forensicRiskScoreEl) {
      forensicRiskScoreEl.textContent = `${forensics.risk_score ?? 0} / 100`;
    }

    if (forensicConfidenceEl) {
      const conf = Math.round((forensics.confidence ?? 0.85) * 100);
      forensicConfidenceEl.textContent = `${conf}%`;
    }

    const metrics = forensics.metrics || {};
    if (metadataSoftwareEl) {
      metadataSoftwareEl.textContent = metrics.software_detected || "Clean / None";
    }

    // Combined Indicators (Rules + Visual Forensics)
    if (forensicIndicatorsEl) {
      forensicIndicatorsEl.innerHTML = "";
      const allIndicators = [];

      // Add document rule indicators
      if (doc.indicators && doc.indicators.length > 0) {
        doc.indicators.forEach(ind => allIndicators.push(ind));
      }

      // Add forensic indicators
      if (forensics.indicators && forensics.indicators.length > 0) {
        forensics.indicators.forEach(ind => {
          if (!allIndicators.includes(ind)) {
            allIndicators.push(ind);
          }
        });
      }

      if (allIndicators.length > 0) {
        allIndicators.forEach((indicator) => {
          const li = document.createElement("li");
          li.textContent = indicator;
          forensicIndicatorsEl.appendChild(li);
        });
      } else {
        const li = document.createElement("li");
        li.textContent = "Clean Baseline: No compression anomalies, digital editor signatures, or identity mismatches detected.";
        forensicIndicatorsEl.appendChild(li);
      }
    }

    // Technical Metrics Matrix
    const elaEl = document.getElementById("metricEla");
    const sharpEl = document.getElementById("metricSharpness");
    const aspectEl = document.getElementById("metricAspectRatio");
    const resEl = document.getElementById("metricResolution");

    if (elaEl) elaEl.textContent = metrics.ela_score ?? "--";
    if (sharpEl) sharpEl.textContent = metrics.sharpness_variance ?? "--";
    if (aspectEl) aspectEl.textContent = metrics.aspect_ratio ?? "--";
    if (resEl) resEl.textContent = metrics.resolution ?? "--";
  }

  function getRiskTagClass(level) {
    const l = (level || "").toLowerCase();
    if (l.includes("low")) return "tag-low";
    if (l.includes("medium")) return "tag-medium";
    if (l.includes("high")) return "tag-high";
    return "tag-unknown";
  }

  function getGaugeBarClass(level) {
    const l = (level || "").toLowerCase();
    if (l.includes("low")) return "bar-low";
    if (l.includes("medium")) return "bar-medium";
    if (l.includes("high")) return "bar-high";
    return "";
  }

  function getDirectiveClass(level) {
    const l = (level || "").toLowerCase();
    if (l.includes("low")) return "dir-low";
    if (l.includes("medium")) return "dir-medium";
    if (l.includes("high")) return "dir-high";
    return "";
  }
});
