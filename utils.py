import re
import cv2
import pytesseract
from rapidfuzz import fuzz

# =========================================================
# DOCUMENT BOILERPLATE & REGULATORY KEYWORDS
# =========================================================

BOILERPLATE_WORDS = {
    "income", "tax", "department", "govt", "government", "india", "permanent",
    "account", "number", "father", "fathers", "name", "card", "signature",
    "date", "birth", "dob", "male", "female", "uidai", "unique", "identification",
    "authority", "mera", "aadhaar", "pe पहचान", "help@uidai.gov.in", "download",
    "republic", "visa", "passport", "entry", "entries", "valid", "expiry", "issue",
    "of", "the", "in", "and", "for", "to", "at", "pan", "holder", "citizen", "union"
}

AUTHORITY_KEYWORDS = {
    "pan": ["income tax", "govt. of india", "government of india", "permanent account", "incometax"],
    "aadhaar": ["unique identification", "uidai", "government of india", "bharat sarkar", "mera aadhaar", "enrolment"],
    "visa": ["visa", "passport", "entry", "entries", "valid", "immigration", "republic"]
}


# =========================================================
# OCR EXTRACTION
# =========================================================

def extract_text_from_image(filepath):
    """
    Extract text using OpenCV adaptive preprocessing and Tesseract OCR.
    """
    image = cv2.imread(filepath)

    if image is None:
        return ""

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    _, thresh = cv2.threshold(
        resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    text = pytesseract.image_to_string(thresh)

    return text


def normalize_text(text):
    if not text:
        return ""

    text = text.lower()
    text = " ".join(text.split())
    return text


# =========================================================
# INTELLIGENT IDENTITY & NAME MATCHING
# =========================================================

def extract_best_name_match(user_name, extracted_text, doc_number=None):
    """
    Extracts candidate name lines from OCR text, cleans document boilerplate,
    and calculates multi-metric similarity against the user's claimed name.

    Returns:
        similarity (int 0-100),
        detected_name (str or None),
        status_label (str)
    """
    if not user_name or not extracted_text:
        return 0, None, "No Name Provided"

    working_text = extracted_text
    if doc_number:
        # Strip document number from text so it does not pollute name matching
        working_text = re.sub(re.escape(str(doc_number)), " ", working_text, flags=re.IGNORECASE)

    user_norm = " ".join(user_name.lower().split())
    lines = [l.strip() for l in working_text.splitlines() if l.strip()]

    candidates = []
    for line in lines:
        words = line.split()
        cleaned_words = [re.sub(r"[^a-zA-Z]", "", w).lower() for w in words]
        filtered_words = [w for w in cleaned_words if len(w) >= 2 and w not in BOILERPLATE_WORDS]

        if filtered_words:
            cand_clean = " ".join(filtered_words)
            orig_words = [w for w in words if re.sub(r"[^a-zA-Z]", "", w).lower() not in BOILERPLATE_WORDS and not any(c.isdigit() for c in w)]
            orig_display = " ".join(orig_words) if orig_words else line
            candidates.append((cand_clean, orig_display))

    best_score = 0
    best_detected = None

    for cand_clean, orig_display in candidates:
        s1 = fuzz.ratio(user_norm, cand_clean)
        s2 = fuzz.token_sort_ratio(user_norm, cand_clean)
        s3 = 100 if user_norm in cand_clean else fuzz.partial_ratio(user_norm, cand_clean)

        line_score = max(s1, s2, int(s3 * 0.9))
        if line_score > best_score:
            best_score = line_score
            best_detected = orig_display

    # Fallback check against concatenated non-boilerplate text
    if best_score < 60:
        all_cleaned = " ".join([c[0] for c in candidates])
        if all_cleaned:
            ts = fuzz.token_set_ratio(user_norm, all_cleaned)
            if ts > 80:
                best_score = max(best_score, ts)

    similarity = min(100, int(round(best_score)))

    # Determine descriptive identity status
    if similarity >= 85:
        status_label = "Match"
    elif similarity >= 70:
        status_label = "Minor Discrepancy"
    elif similarity >= 50:
        status_label = "Moderate Discrepancy"
    else:
        status_label = "Severe Mismatch (Impersonation Alert)"

    return similarity, best_detected, status_label


def get_name_similarity(user_name, extracted_text):
    """
    Backwards compatibility helper: returns integer similarity percentage.
    """
    similarity, _, _ = extract_best_name_match(user_name, extracted_text)
    return similarity


# =========================================================
# AUTHORITY KEYWORD & REGULATORY VERIFICATION
# =========================================================

def check_mandatory_authority_keywords(document_type, extracted_text):
    """
    Checks if official issuing authority keywords are present on the document.
    Fake documents often lack official headers, logos, and issuing department text.
    """
    if not extracted_text:
        return False, []

    text_lower = extracted_text.lower()
    expected = AUTHORITY_KEYWORDS.get(document_type, [])

    found = []
    for kw in expected:
        if kw in text_lower:
            found.append(kw)

    # Valid if at least 1 primary issuing authority keyword is detected
    is_valid = len(found) >= 1
    return is_valid, found


# =========================================================
# RISK SCORING ENGINE
# =========================================================

def calculate_risk_score(document_status, name_similarity,
                         document_format_valid, checksum_valid=True,
                         entity_valid=True, authority_valid=True):
    """
    Calculates deterministic rule-based risk score (0 to 100).

    Heavily penalizes identity mismatches (< 50% name similarity) to prevent
    impersonation where a fraudster uses someone else's genuine document.
    """
    score = 0

    # 1. Document number validation
    if "mismatch" in document_status.lower():
        score += 50
    elif "not detected" in document_status.lower():
        score += 40

    # 2. Identity / Name matching (CRITICAL FOR IMPERSONATION DETECTION)
    if name_similarity < 50:
        # Severe name mismatch: claimed person is different from document cardholder!
        score += 65
    elif name_similarity < 70:
        # Significant name discrepancy
        score += 40
    elif name_similarity < 85:
        # Minor typo / abbreviation
        score += 15

    # 3. Document format validation (Regex syntax)
    if not document_format_valid:
        score += 25

    # 4. Mathematical checksum validation (Verhoeff for Aadhaar)
    if not checksum_valid:
        score += 25

    # 5. Entity code validation (PAN 4th character)
    if not entity_valid:
        score += 20

    # 6. Issuing authority keywords validation
    if not authority_valid:
        score += 25

    return min(100, max(0, score))


def get_risk_level(score):
    if score >= 50:
        return "High Risk"
    elif score >= 20:
        return "Medium Risk"

    return "Low Risk"


# =========================================================
# CENTRAL VERIFICATION ENGINE
# =========================================================

def verify_document(document_type, name, document_number, extracted_text):
    """
    Evaluates document number, name similarity, regulatory format,
    authority keywords, and structural integrity.
    """
    # 1. Authority keywords check
    authority_valid, found_keywords = check_mandatory_authority_keywords(
        document_type, extracted_text
    )

    # 2. Extract Document Number and Validate Format
    extracted_document = None
    document_status = "Unknown"
    document_format_valid = False
    checksum_valid = True
    entity_valid = True
    indicators = []

    if document_type == "pan":
        from validators.pan import (
            extract_pan, validate_pan, validate_pan_format,
            validate_pan_entity, validate_pan_surname
        )

        extracted_document = extract_pan(extracted_text)
        document_status = validate_pan(document_number, extracted_document)
        document_format_valid = validate_pan_format(extracted_document or document_number)

        # Entity code check
        target_pan = extracted_document or document_number
        is_ent_valid, ent_desc = validate_pan_entity(target_pan)
        entity_valid = is_ent_valid
        if not is_ent_valid:
            indicators.append(f"Invalid PAN Entity: 4th character in '{target_pan}' is not a recognized entity type.")

        # Surname check for individuals
        surname_match = validate_pan_surname(target_pan, name)
        if surname_match is False:
            indicators.append(f"PAN Surname Discrepancy: 5th character in '{target_pan}' does not match claimed surname initial.")

    elif document_type == "aadhaar":
        from validators.aadhaar import (
            extract_aadhaar, validate_aadhaar, validate_aadhaar_format,
            validate_verhoeff_checksum
        )

        extracted_document = extract_aadhaar(extracted_text)
        document_status = validate_aadhaar(document_number, extracted_document)
        document_format_valid = validate_aadhaar_format(extracted_document or document_number)

        # Verhoeff mathematical checksum validation
        target_aadhaar = extracted_document or document_number
        checksum_valid = validate_verhoeff_checksum(target_aadhaar)
        if not checksum_valid:
            indicators.append(f"Aadhaar Checksum Failure: 12-digit sequence '{target_aadhaar}' failed UIDAI Verhoeff mathematical checksum.")

    elif document_type == "visa":
        from validators.visa import (
            extract_visa_number, validate_visa, validate_visa_format
        )

        extracted_document = extract_visa_number(extracted_text)
        document_status = validate_visa(document_number, extracted_document)
        document_format_valid = validate_visa_format(extracted_document or document_number)

    else:
        return {"success": False, "error": "Invalid document type"}

    # 3. Intelligent Name Matching (with document number stripped)
    name_similarity, detected_name, name_status = extract_best_name_match(
        name, extracted_text, doc_number=(extracted_document or document_number)
    )

    if name_similarity < 50:
        indicators.append(f"Critical Identity Mismatch: Claimed name '{name}' does not match cardholder name detected on document ('{detected_name or 'Unrecognized'}', {name_similarity}% similarity).")
    elif name_similarity < 70:
        indicators.append(f"Name Discrepancy: Claimed name '{name}' has only {name_similarity}% similarity with detected name '{detected_name or 'Unknown'}'.")

    # 4. Authority header warnings
    if not authority_valid:
        indicators.append(f"Missing Authority Headers: No standard issuing authority keywords for {document_type.upper()} detected.")

    # 5. Number match determination
    number_match = (
        "match" in document_status.lower()
        and "mismatch" not in document_status.lower()
    )

    if not number_match and "mismatch" in document_status.lower():
        indicators.append(f"Document Number Mismatch: Entered '{document_number}', but OCR extracted '{extracted_document}'.")

    # 6. Rule Risk Score Calculation
    risk_score = calculate_risk_score(
        document_status,
        name_similarity,
        document_format_valid,
        checksum_valid=checksum_valid,
        entity_valid=entity_valid,
        authority_valid=authority_valid
    )

    risk_level = get_risk_level(risk_score)

    return {
        "success": True,
        "document": {
            "type": document_type,
            "entered_number": document_number,
            "detected_number": extracted_document,
            "number_match": number_match,
            "format_valid": document_format_valid,
            "checksum_valid": checksum_valid,
            "entity_valid": entity_valid,
            "authority_valid": authority_valid,
            "indicators": indicators
        },
        "identity": {
            "entered_name": name,
            "detected_name": detected_name,
            "name_similarity": name_similarity,
            "name_status": name_status,
            "is_impersonation_risk": (name_similarity < 50)
        },
        "risk": {
            "score": risk_score,
            "level": risk_level
        }
    }


def process_document(document_type, name, document_number, filepath):
    extracted_text = extract_text_from_image(filepath)

    if not extracted_text or not extracted_text.strip():
        return {
            "success": False,
            "error": "Could not extract text from document"
        }

    result = verify_document(document_type, name, document_number, extracted_text)
    return result


# =========================================================
# COMBINED RISK SYNTHESIS WITH SAFETY GATES
# =========================================================

def calculate_combined_risk(rule_risk, forensic_risk, name_similarity=100, number_match=True, format_valid=True):
    """
    Combines rule-based verification (60%) and algorithmic OpenCV forensics (40%).

    CRITICAL SECURITY GATES:
    - If name_similarity < 50 (Impersonation): Guarantees minimum High Risk (>= 75).
    - If number_match is False: Guarantees minimum High Risk (>= 65).
    - If format_valid is False: Guarantees minimum High Risk (>= 55).
    - If 50 <= name_similarity < 70: Guarantees minimum Medium Risk (>= 45).
    """
    combined_score = (rule_risk * 0.6) + (forensic_risk * 0.4)

    # 1. Identity impersonation override
    if name_similarity < 50:
        combined_score = max(combined_score, 75)
    elif name_similarity < 70:
        combined_score = max(combined_score, 45)

    # 2. Document number mismatch override
    if not number_match:
        combined_score = max(combined_score, 65)

    # 3. Invalid regex syntax override
    if not format_valid:
        combined_score = max(combined_score, 55)

    return min(100, max(0, round(combined_score)))


def get_combined_risk_level(score):
    if score >= 50:
        return "High Risk"
    elif score >= 20:
        return "Medium Risk"

    return "Low Risk"


# =========================================================
# EXPLANATION & OPERATIONAL DIRECTIVE
# =========================================================

def get_recommended_next_step(risk_level, name_similarity=100, number_match=True):
    """
    Provide actionable screening guidance based on the assigned risk level and specific red flags.
    """
    level = (risk_level or "").lower()

    if name_similarity < 50:
        return "Reject automated screening. Immediate escalation for in-person identity verification. Claimed name does not match document credentials (possible impersonation)."

    if not number_match:
        return "Escalate for manual inspection. Document identifier on image does not match the entered credentials."

    if "high" in level:
        return "Escalate for manual inspection. Request original physical document and secondary government identity proof due to high forensic/structural risk."
    elif "medium" in level:
        return "Secondary review recommended. Cross-check identity spelling discrepancy and verify document under enhanced lighting."

    return "Standard document processing approved. Credential identifiers, name, and visual pixel forensics pass preliminary screening."


def generate_explanation(doc_result, forensic_result, final_risk_level):
    """
    Generate a human-readable summary explaining why a risk score was assigned.
    """
    reasons = []

    # 1. Identity / Name check
    identity_info = doc_result.get("identity", {})
    name_sim = identity_info.get("name_similarity", 0)
    entered_name = identity_info.get("entered_name", "")
    detected_name = identity_info.get("detected_name")

    if name_sim < 50:
        if detected_name:
            reasons.append(f"CRITICAL IDENTITY MISMATCH: The claimed name '{entered_name}' does not match the name detected on the document ('{detected_name}', {name_sim}% similarity). Potential identity impersonation attempt.")
        else:
            reasons.append(f"CRITICAL IDENTITY MISMATCH: The claimed name '{entered_name}' was not detected in the document text ({name_sim}% similarity).")
    elif name_sim < 70:
        reasons.append(f"Name Discrepancy: Moderate difference between claimed name '{entered_name}' and detected text ('{detected_name or 'Unknown'}', {name_sim}% similarity).")
    elif name_sim < 85:
        reasons.append(f"Minor name spelling variation ({name_sim}% similarity).")
    else:
        reasons.append(f"Cardholder name matches the claimed identity ({name_sim}% similarity).")

    # 2. Document number check
    doc_info = doc_result.get("document", {})
    detected_num = doc_info.get("detected_number")
    num_match = doc_info.get("number_match")
    format_valid = doc_info.get("format_valid")
    checksum_valid = doc_info.get("checksum_valid", True)
    authority_valid = doc_info.get("authority_valid", True)

    if not detected_num:
        reasons.append("Document identifier was not detected in the document image.")
    elif not num_match:
        reasons.append(f"Document number mismatch (detected '{detected_num}' vs entered).")
    else:
        reasons.append(f"Document number ({detected_num}) matches the entered credentials.")

    if detected_num and not format_valid:
        reasons.append("Document number does not satisfy standard alphanumeric syntax.")

    if not checksum_valid:
        reasons.append("Aadhaar Verhoeff mathematical checksum verification failed.")

    if not authority_valid:
        reasons.append("Official issuing authority keywords were absent from the document.")

    # 3. OpenCV Image Forensics check
    if forensic_result:
        if forensic_result.get("suspicious"):
            indicators = forensic_result.get("indicators", [])
            if indicators:
                reasons.append(f"Visual forensics flagged: {'; '.join(indicators)}.")
            else:
                reasons.append("Visual forensics flagged potential tampering anomalies.")
        else:
            reasons.append("Visual pixel forensics detected no compression or structural manipulation.")

    return " ".join(reasons)
