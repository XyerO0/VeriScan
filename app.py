from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from forensics import analyze_document_forensics

import os
import uuid

from utils import (
    process_document,
    calculate_combined_risk,
    get_combined_risk_level,
    generate_explanation,
    get_recommended_next_step
)


app = Flask(__name__)


# =========================================================
# CONFIGURATION
# =========================================================

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


@app.after_request
def add_cache_control_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# =========================================================
# FILE VALIDATION
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_uploaded_file(file):

    original_filename = secure_filename(file.filename)

    extension = original_filename.rsplit(".", 1)[1].lower()

    filename = str(uuid.uuid4()) + "." + extension

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    return filepath, filename


def delete_file(filepath):

    try:

        if os.path.exists(filepath):

            os.remove(filepath)

    except OSError as e:

        print(f"Could not delete file: {e}")


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# WEB VERIFICATION
# =========================================================

@app.route("/verify", methods=["GET", "POST"])
def verify():

    if request.method == "GET":

        return render_template("verify.html")


    # -----------------------------------------
    # Get form data
    # -----------------------------------------

    docType = request.form.get("documentType")

    name = request.form.get("name")

    document = request.form.get("document")


    # -----------------------------------------
    # Validate document type
    # -----------------------------------------

    if docType not in ["pan", "aadhaar", "visa"]:

        return render_template(
            "verify.html",
            error="Invalid document type"
        )


    # -----------------------------------------
    # Validate name
    # -----------------------------------------

    if not name or not name.strip():

        return render_template(
            "verify.html",
            error="Name is required"
        )


    # -----------------------------------------
    # Validate document number
    # -----------------------------------------

    if not document or not document.strip():

        return render_template(
            "verify.html",
            error="Document number is required"
        )


    # -----------------------------------------
    # Get file
    # -----------------------------------------

    file = request.files.get("documentFile")

    if not file:

        return render_template(
            "verify.html",
            error="No file uploaded"
        )

    if file.filename == "":

        return render_template(
            "verify.html",
            error="No file selected"
        )


    # -----------------------------------------
    # Validate extension
    # -----------------------------------------

    if not allowed_file(file.filename):

        return render_template(
            "verify.html",
            error="Invalid file type"
        )


    # -----------------------------------------
    # Save file
    # -----------------------------------------

    filepath, filename = save_uploaded_file(file)


    try:

        # -----------------------------------------
        # Process document
        # -----------------------------------------

        result = process_document(
            docType,
            name,
            document,
            filepath
        )


        # -----------------------------------------
        # Processing error
        # -----------------------------------------

        if not result["success"]:

            return render_template(
                "verify.html",
                error=result["error"]
            )


        # -----------------------------------------
        # Image Forensics analysis (OpenCV + PIL)
        # -----------------------------------------

        try:
            forensic_result = analyze_document_forensics(
                filepath,
                docType
            )

        except Exception as e:
            print("Forensic analysis error:", e)

            forensic_result = {
                "status": "error",
                "suspicious": False,
                "confidence": 0,
                "risk_score": 0,
                "indicators": ["Forensic analysis encountered an unexpected error"],
                "metrics": {
                    "ela_score": 0,
                    "sharpness_variance": 0,
                    "aspect_ratio": 0,
                    "resolution": "unknown",
                    "software_detected": None
                }
            }


        # -----------------------------------------
        # Combined Risk & Screening Assessment
        # -----------------------------------------

        rule_risk = result["risk"]["score"]
        forensic_risk = forensic_result["risk_score"]
        name_similarity = result["identity"]["name_similarity"]
        number_match = result["document"]["number_match"]
        format_valid = result["document"]["format_valid"]

        combined_risk = calculate_combined_risk(
            rule_risk,
            forensic_risk,
            name_similarity=name_similarity,
            number_match=number_match,
            format_valid=format_valid
        )
        final_risk_score = combined_risk
        final_risk_level = get_combined_risk_level(combined_risk)

        explanation = generate_explanation(
            result,
            forensic_result,
            final_risk_level
        )

        recommended_next_step = get_recommended_next_step(
            final_risk_level,
            name_similarity=name_similarity,
            number_match=number_match
        )


        # -----------------------------------------
        # Display result
        # -----------------------------------------

        return render_template(
            "verify.html",

            docType=docType,

            name=name,

            document=document,

            filename=filename,

            extracted_document=result["document"]["detected_number"],

            document_status=result["document"]["number_match"],

            detected_name=result["identity"].get("detected_name"),

            name_status=result["identity"].get("name_status"),

            name_similarity=result["identity"]["name_similarity"],

            document_format_valid=result["document"]["format_valid"],

            authority_valid=result["document"].get("authority_valid", True),

            checksum_valid=result["document"].get("checksum_valid", True),

            risk_score=final_risk_score,

            risk_level=final_risk_level,

            forensic_analysis=forensic_result,

            explanation=explanation,

            recommended_next_step=recommended_next_step,

            status="Analysis Complete"
        )

    finally:

        # -----------------------------------------
        # Delete uploaded file
        # -----------------------------------------

        delete_file(filepath)


# =========================================================
# API VERIFICATION
# =========================================================

@app.route("/api/verify", methods=["POST"])
def api_verify():


    # -----------------------------------------
    # Get form data
    # -----------------------------------------

    docType = request.form.get("documentType")

    name = request.form.get("name")

    document = request.form.get("document")


    # -----------------------------------------
    # Validate document type
    # -----------------------------------------

    if docType not in ["pan", "aadhaar", "visa"]:

        return {
            "success": False,
            "error": "Invalid document type"
        }, 400


    # -----------------------------------------
    # Validate name
    # -----------------------------------------

    if not name or not name.strip():

        return {
            "success": False,
            "error": "Name is required"
        }, 400


    # -----------------------------------------
    # Validate document number
    # -----------------------------------------

    if not document or not document.strip():

        return {
            "success": False,
            "error": "Document number is required"
        }, 400


    # -----------------------------------------
    # Get file
    # -----------------------------------------

    file = request.files.get("documentFile")

    if not file:

        return {
            "success": False,
            "error": "No file uploaded"
        }, 400

    if file.filename == "":

        return {
            "success": False,
            "error": "No file selected"
        }, 400


    # -----------------------------------------
    # Validate extension
    # -----------------------------------------

    if not allowed_file(file.filename):

        return {
            "success": False,
            "error": "Invalid file type"
        }, 400


    # -----------------------------------------
    # Save file
    # -----------------------------------------

    filepath, filename = save_uploaded_file(file)


    try:

        # -----------------------------------------
        # Process document
        # -----------------------------------------

        result = process_document(
            docType,
            name,
            document,
            filepath
        )


        # -----------------------------------------
        # Processing error
        # -----------------------------------------

        if not result["success"]:

            return result, 400


        # -----------------------------------------
        # Image Forensics analysis (OpenCV + PIL)
        # -----------------------------------------

        try:
            forensic_result = analyze_document_forensics(
                filepath,
                docType
            )

        except Exception as e:
            print("Forensic analysis error:", e)

            forensic_result = {
                "status": "error",
                "suspicious": False,
                "confidence": 0,
                "risk_score": 0,
                "indicators": ["Forensic analysis encountered an unexpected error"],
                "metrics": {
                    "ela_score": 0,
                    "sharpness_variance": 0,
                    "aspect_ratio": 0,
                    "resolution": "unknown",
                    "software_detected": None
                }
            }


        # -----------------------------------------
        # Add Forensics result to existing result
        # -----------------------------------------

        result["forensic_analysis"] = forensic_result

        # Backwards compatibility alias for consumers expecting ai_analysis
        result["ai_analysis"] = {
            "status": "replaced_by_forensics",
            "suspicious": forensic_result["suspicious"],
            "confidence": forensic_result["confidence"],
            "risk_score": forensic_result["risk_score"],
            "reasons": forensic_result["indicators"]
        }

        rule_risk = result["risk"]["score"]
        forensic_risk = forensic_result["risk_score"]
        name_similarity = result["identity"]["name_similarity"]
        number_match = result["document"]["number_match"]
        format_valid = result["document"]["format_valid"]

        combined_risk = calculate_combined_risk(
            rule_risk,
            forensic_risk,
            name_similarity=name_similarity,
            number_match=number_match,
            format_valid=format_valid
        )

        final_risk = {
            "score": combined_risk,
            "level": get_combined_risk_level(combined_risk),
            "forensics_included": True
        }

        result["final_risk"] = final_risk

        # -----------------------------------------
        # Generate Explanation & Recommended Next Step
        # -----------------------------------------

        explanation = generate_explanation(
            result,
            forensic_result,
            final_risk["level"]
        )

        recommended_next_step = get_recommended_next_step(
            final_risk["level"],
            name_similarity=name_similarity,
            number_match=number_match
        )

        result["explanation"] = explanation
        result["recommended_next_step"] = recommended_next_step
        final_risk["explanation"] = explanation
        final_risk["recommended_next_step"] = recommended_next_step


        # -----------------------------------------
        # Return final result
        # -----------------------------------------

        return result, 200


    finally:

        # -----------------------------------------
        # Delete uploaded file
        # -----------------------------------------

        delete_file(filepath)


# =========================================================
# HEALTH-CHECK
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():

    return {
        "success": True,
        "status": "Backend is running"
    }, 200


# =========================================================
# FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    return {
        "success": False,
        "error": "File is too large. Maximum size is 5 MB."
    }, 413


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)

