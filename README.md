# VeriScan — Identity Document & Forensic Screening System

<div align="center">

![VeriScan Banner](static/favicon.svg)

### *Locally Powered Algorithmic Document Verification & Fraud Screening Terminal*

[![SIH 2026](https://img.shields.io/badge/Smart%20India%20Hackathon-2026-f59e0b?style=for-the-badge&logo=target)](https://sih.gov.in/)
[![Team](https://img.shields.io/badge/Team-VibexLeapers-3b82f6?style=for-the-badge)](https://github.com/XyerO0/VeriScan)
[![Python](https://img.shields.io/badge/Python-3.10%20|%203.11%20|%203.12-blue?style=for-the-badge&logo=python)](https://python.org)
[![Framework](https://img.shields.io/badge/Backend-Flask%203.x-10b981?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![Computer Vision](https://img.shields.io/badge/Forensics-OpenCV%20%2B%20PIL-red?style=for-the-badge&logo=opencv)](https://opencv.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Zero%20Database%20%2F%20100%25%20Local-8b5cf6?style=for-the-badge)](#core-principles)

</div>

---

## Technical Positioning

> **"A locally powered algorithmic system for preliminary screening of identity documents and identification of potentially suspicious indicators."**
> 
> *VeriScan is a rapid-response, client-free screening tool designed for the Smart India Hackathon (SIH). It performs pixel-level image forensics and deterministic rule validation in-memory. It does not interface with government databases and does not claim 100% legal authenticity determination.*

---

## Overview

Identity fraud and document tampering have evolved beyond simple document replacements. Fraudsters now use digital editing tools (Photoshop, Canva, MS Paint) to splice names, edit dates of birth, swap headshots, and spoof identity credentials.

**VeriScan** provides an air-gapped, zero-cloud preliminary screening terminal. It analyzes physical and digital identity credentials (including **Indian PAN Cards**, **Aadhaar Cards**, and **Travel Visas**) using a dual-track verification pipeline:

1. **Deterministic Rule & Identity Integrity**: Mathematical checksum algorithms, syntax regex validation, issuing authority headers, and fuzzy Levenshtein candidate name extraction.
2. **Algorithmic Computer Vision Forensics**: Error Level Analysis (ELA), 3×3 Laplacian sharpness variance grids, digital text box boundary detection, sensor noise uniformity analysis, and EXIF metadata software audits.

---

## System Architecture

```text
                                [ User / Inspector ]
                                          │
                                 (Upload Image & Claim)
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │    VeriScan Ingestion Console   │
                         │    (Flask / Stateless Runtime)  │
                         └─────────────────────────────────┘
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 ▼                                                 ▼
  ┌─────────────────────────────┐                  ┌───────────────────────────────┐
  │   TRACK 1: OCR & IDENTITY   │                  │   TRACK 2: IMAGE FORENSICS    │
  │   (Tesseract + RapidFuzz)   │                  │        (OpenCV + PIL)         │
  ├─────────────────────────────┤                  ├───────────────────────────────┤
  │ • Adaptive Thresholding     │                  │ • Error Level Analysis (ELA)  │
  │ • Candidate Name Extraction │                  │ • 3x3 Laplacian Sharpness Var │
  │ • Regex Syntax Validation   │                  │ • Digital Patch & Box Canny   │
  │ • Aadhaar Verhoeff Checksum │                  │ • Sensor Noise Uniformity     │
  │ • PAN Entity & Surname Bind │                  │ • ISO/IEC 7810 ID-1 Ratio     │
  │ • Issuing Authority Headers │                  │ • EXIF Software Metadata      │
  └─────────────────────────────┘                  └───────────────────────────────┘
                 │                                                 │
                 └────────────────────────┬────────────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │   Risk Synthesis & Assessment   │
                         │   (Weighted 60/40 + Gate Floors)│
                         └─────────────────────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │    Live Telemetry Dashboard     │
                         │  • Risk Index (0 - 100)         │
                         │  • Risk Level (Low/Med/High)    │
                         │  • Flagged Anomaly Indicators   │
                         │  • Operational Next Step        │
                         │  • Full Screening Narrative     │
                         └─────────────────────────────────┘
```

---

## Core Capabilities & Forensic Defenses

### 1. Intelligent Identity & Impersonation Gate
* **Boilerplate Filtering**: Strips out document numbers and official text (`INCOME TAX DEPARTMENT`, `GOVT OF INDIA`, `UIDAI`, `PERMANENT ACCOUNT NUMBER`) to isolate the actual cardholder name.
* **Candidate Line Matching**: Evaluates candidate names using token sort ratios, Levenshtein distances, and direct substring comparisons.
* **Impersonation Override**: If the claimed name does not match the cardholder name (`< 50%` similarity), the system triggers a **Critical Impersonation Alert** and forces a minimum **High Risk** rating ($\ge 75$), even if the document number is valid.

### 2. UIDAI Aadhaar Verhoeff Checksum Validation
* Implements the official **Verhoeff algorithm** based on dihedral group $D_5$ permutations.
* Validates whether the 12th digit of an Aadhaar number satisfies the mathematical checksum of the preceding 11 digits, immediately flagging randomly generated 12-digit fake cards.

### 3. PAN Structural & Entity Verification
* **4th Character Entity Validation**: Verifies that the 4th character matches official Income Tax Department entity classifications (`P` for Individual, `C` for Company, `H` for HUF, `F` for Firm, etc.).
* **5th Character Surname Binding**: For individual PAN cards (`P`), verifies that the 5th character matches the initial letter of the applicant's claimed surname.

### 4. Error Level Analysis (ELA)
* Recompresses image data to 90% JPEG quality in-memory and computes absolute pixel difference matrices.
* Analyzes a 4×4 spatial grid to detect compression disparities, identifying spliced numbers or modified text overlays.

### 5. 3×3 Laplacian Sharpness & Splicing Grid
* Computes localized Laplacian variance across 9 partitioned document sectors.
* Detects digital text overlays that have abnormally crisp edges compared to a degraded, scanned background card.

### 6. Digital Patch & Sensor Noise Uniformity
* **Canny Boundary Detection**: Identifies sharp rectangular contour boxes with uniform internal fill typical of copy-pasted text boxes.
* **High-Pass Noise Distribution**: Measures high-frequency sensor noise across image blocks. Genuine camera/scanned documents have uniform noise; digitally generated patches contain zero-noise flat regions.

### 7. ISO/IEC 7810 ID-1 Standard Geometry
* Evaluates bounding aspect ratios against standard credit card dimensions (target ratio: **1.586**, $85.60 \times 53.98\text{ mm}$).

### 8. EXIF Metadata Software Audit
* Probes binary image headers for signatures of image editing tools (Adobe Photoshop, GIMP, Canva, Snapseed, Lightroom, Pixlr).

---

## Document Specification Reference Matrix

| Document Standard | Issuing Authority | Format Syntax | Target Aspect Ratio | Primary Fraud & Tamper Vectors |
| :--- | :--- | :--- | :--- | :--- |
| **Indian PAN Card** | Income Tax Department | `^[A-Z]{5}[0-9]{4}[A-Z]$` | **1.586** (ID-1 Standard) | Digit alteration, 4th char entity spoofing, surname mismatch |
| **Aadhaar Card** | UIDAI | `^\d{12}$` (Verhoeff $D_5$) | **1.586** (Card / Cutout) | Verhoeff checksum failure, headshot splicing, font mismatch |
| **Travel Visa** | Immigration Department | `^[A-Z0-9]{5,20}$` | **1.414** (ISO 216 / A6) | Expiration date alteration, digital stamp insertion |

---

## Screening Assessment Output

VeriScan provides four standardized screening telemetry components:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ RISK INDEX: 75 / 100                 RISK LEVEL: HIGH RISK             │
├────────────────────────────────────────────────────────────────────────┤
│ OPERATIONAL DIRECTIVE:                                                 │
│ Reject automated screening. Immediate escalation for in-person         │
│ identity verification. Claimed name does not match document           │
│ credentials (possible impersonation).                                  │
├────────────────────────────────────────────────────────────────────────┤
│ FLAGGED ANOMALIES & INDICATORS:                                        │
│ • Critical Identity Mismatch: Claimed 'Vikram Singh' vs 'Rahul Kumar'. │
│ • Document Number (ABCDE1234F) matches entered credentials.            │
│ • Clean Forensic Baseline: No compression anomalies detected.          │
├────────────────────────────────────────────────────────────────────────┤
│ EXPLANATION:                                                           │
│ CRITICAL IDENTITY MISMATCH: The claimed name 'Vikram Singh' does not   │
│ match the name detected on the document ('Rahul Kumar', 31% similarity)│
│ Potential identity impersonation attempt.                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Core Principles

- **NO DATABASE**: Stateless, in-memory pipeline. No user data, images, or extracted text are stored in any database (no SQLite, MySQL, Postgres, MongoDB, or Firebase).
- **PRIVACY FIRST**: Uploaded image artifacts are processed in-memory and deleted immediately upon request completion.
- **ZERO CLOUD DEPENDENCY**: Can run completely air-gapped on standard developer hardware without third-party API keys or internet access.
- **HIGH AUDITABILITY**: Every risk score is mathematically explainable through deterministic criteria and quantitative visual metrics.

---

## Getting Started

### Prerequisites

* **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.14)
* **Tesseract OCR**:
  ```bash
  # Debian / Ubuntu / Pop!_OS
  sudo apt-get update && sudo apt-get install -y tesseract-ocr
  
  # Arch Linux
  sudo pacman -S tesseract tesseract-data-eng
  
  # macOS (Homebrew)
  brew install tesseract
  ```

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/XyerO0/VeriScan.git
   cd VeriScan
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application**:
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://127.0.0.1:5000/`.

---

## Running the Automated Test Suite

VeriScan includes end-to-end automated tests covering rule validation, fuzzy identity matching, Verhoeff checksums, and API endpoints:

```bash
pytest -v
```

Expected output:
```text
tests/test_api.py::test_invalid_document_type PASSED
tests/test_api.py::test_missing_name PASSED
tests/test_api.py::test_missing_document_number PASSED
tests/test_api.py::test_missing_file PASSED
tests/test_api.py::test_health PASSED
tests/test_verification.py::test_pan_match PASSED
tests/test_verification.py::test_pan_mismatch PASSED
tests/test_verification.py::test_pan_not_detected PASSED
tests/test_verification.py::test_name_similarity PASSED
tests/test_verification.py::test_invalid_document_type PASSED
tests/test_verification.py::test_wrong_name_identity_mismatch PASSED
tests/test_verification.py::test_aadhaar_verhoeff_checksum PASSED

============================== 12 passed in 0.35s ==============================
```

---

## Project Structure

```text
projectAlpha/
├── app.py                      # Flask backend, caching headers, REST & web endpoints
├── forensics.py                # OpenCV & PIL algorithmic image forensics engine
├── utils.py                    # OCR parsing, identity matching & risk synthesis
├── validators/
│   ├── aadhaar.py              # Aadhaar format & Verhoeff checksum validation
│   ├── pan.py                  # PAN format, entity code & surname verification
│   └── visa.py                 # Visa format & document identifier extraction
├── templates/
│   ├── index.html              # Forensic console landing page & specification matrix
│   └── verify.html             # Dual-panel ingestion console & telemetry screen
├── static/
│   ├── css/
│   │   └── style.css           # Industrial Forensic Console design system (dark theme)
│   ├── js/
│   │   └── verify.js           # Client interactions, dynamic telemetry & file dropzone
│   └── favicon.svg             # Crosshair inspection vector icon
├── tests/
│   ├── test_api.py             # HTTP endpoint & error handling integration tests
│   └── test_verification.py    # Document verification, Verhoeff & impersonation tests
├── requirements.txt            # Python package dependencies
└── README.md                   # Project documentation & reference guide
```

---

## Team & Hackathon Information

* **Competition**: Smart India Hackathon (SIH) 2026
* **Team**: VibexLeapers
* **Domain**: AI / Computer Vision / Document Security
* **Repository**: [https://github.com/XyerO0/VeriScan](https://github.com/XyerO0/VeriScan)

---

## License

This project is licensed under the MIT License — see the repository for details.
