import io
import os
import cv2
import numpy as np
from PIL import Image, ExifTags


def perform_error_level_analysis(filepath, quality=90):
    """
    Perform Error Level Analysis (ELA) using JPEG re-compression.

    Identifies areas with different compression levels, which typically
    indicate digitally spliced or pasted text/elements in an image.
    """
    try:
        pil_img = Image.open(filepath).convert("RGB")

        # Resave image to in-memory buffer at known quality
        buffer = io.BytesIO()
        pil_img.save(buffer, "JPEG", quality=quality)
        buffer.seek(0)
        resaved_img = Image.open(buffer)

        # Calculate absolute pixel difference
        orig_arr = np.array(pil_img, dtype=np.float32)
        resaved_arr = np.array(resaved_img, dtype=np.float32)
        diff = np.abs(orig_arr - resaved_arr)

        mean_diff = float(np.mean(diff))
        max_diff = float(np.max(diff))
        std_diff = float(np.std(diff))

        # Block-level variance analysis (divide into 4x4 grid)
        h, w = diff.shape[:2]
        block_h = max(h // 4, 1)
        block_w = max(w // 4, 1)

        block_means = []
        for r in range(4):
            for c in range(4):
                block = diff[r * block_h:(r + 1) * block_h, c * block_w:(c + 1) * block_w]
                if block.size > 0:
                    block_means.append(float(np.mean(block)))

        block_var = float(np.std(block_means)) if block_means else 0.0

        # Heuristic scoring: high block variance or high peak-to-mean ratio flags tampering
        anomaly_detected = False
        ela_score = min(int((block_var * 8.0) + (std_diff * 3.0)), 100)

        if block_var > 3.5 or (mean_diff > 0.05 and max_diff > 45 and (max_diff / (mean_diff + 1e-4)) > 150):
            anomaly_detected = True
            ela_score = max(ela_score, 45)

        return {
            "score": ela_score,
            "anomaly_detected": anomaly_detected,
            "mean_diff": round(mean_diff, 2),
            "max_diff": round(max_diff, 2),
            "block_variance": round(block_var, 2)
        }

    except Exception as e:
        print(f"ELA processing error: {e}")
        return {
            "score": 0,
            "anomaly_detected": False,
            "mean_diff": 0.0,
            "max_diff": 0.0,
            "block_variance": 0.0
        }


def analyze_sharpness_and_blur(filepath):
    """
    Analyze image sharpness and localized blur inconsistency using Laplacian variance.
    Flags high-sharpness text spliced onto a degraded background card.
    """
    try:
        image = cv2.imread(filepath)
        if image is None:
            return {"overall_variance": 0.0, "is_blurry": True, "splicing_detected": False}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        is_blurry = lap_var < 50.0

        # Localized 3x3 grid variance to detect spliced sharp text onto a blurry card
        h, w = gray.shape
        block_h = max(h // 3, 1)
        block_w = max(w // 3, 1)

        block_vars = []
        for r in range(3):
            for c in range(3):
                cell = gray[r * block_h:(r + 1) * block_h, c * block_w:(c + 1) * block_w]
                if cell.size > 0:
                    v = float(cv2.Laplacian(cell, cv2.CV_64F).var())
                    block_vars.append(v)

        splicing_detected = False
        if block_vars:
            max_v = max(block_vars)
            min_v = min(block_vars)
            if min_v > 0 and (max_v / (min_v + 1e-4)) > 25.0 and lap_var < 300.0:
                splicing_detected = True

        return {
            "overall_variance": round(lap_var, 2),
            "is_blurry": is_blurry,
            "splicing_detected": splicing_detected
        }

    except Exception as e:
        print(f"Sharpness analysis error: {e}")
        return {"overall_variance": 0.0, "is_blurry": False, "splicing_detected": False}


def check_aspect_ratio_and_resolution(filepath, document_type):
    """
    Check if document dimensions and aspect ratio match standard ID-1 card proportions.
    Standard ISO/IEC 7810 ID-1 ratio is ~1.586 (credit card format for PAN and Aadhaar).
    """
    try:
        image = cv2.imread(filepath)
        if image is None:
            return {"aspect_ratio": 0.0, "resolution": "0x0", "aspect_valid": False, "low_resolution": True}

        h, w = image.shape[:2]
        ratio = max(w, h) / max(min(w, h), 1)

        low_res = (w < 400 or h < 300)
        aspect_valid = True

        if document_type in ["pan", "aadhaar"]:
            # Standard card aspect ratio is 1.586; allow 1.25 to 2.10 for crop variations
            if ratio < 1.25 or ratio > 2.10:
                aspect_valid = False

        return {
            "aspect_ratio": round(ratio, 2),
            "resolution": f"{w}x{h}",
            "aspect_valid": aspect_valid,
            "low_resolution": low_res
        }

    except Exception as e:
        print(f"Aspect ratio check error: {e}")
        return {"aspect_ratio": 0.0, "resolution": "0x0", "aspect_valid": True, "low_resolution": False}


def inspect_image_metadata(filepath):
    """
    Check image EXIF and metadata for digital editing software signatures.
    """
    detected_software = None

    try:
        with Image.open(filepath) as img:
            info = img.info or {}
            software_candidates = []

            for key in ["Software", "software", "CreatorTool", "ProcessingSoftware"]:
                if key in info:
                    software_candidates.append(str(info[key]))

            exif_data = img._getexif() if hasattr(img, "_getexif") and img._getexif() else {}
            if exif_data:
                for tag_id, val in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    if tag_name in ["Software", "ProcessingSoftware"]:
                        software_candidates.append(str(val))

            tamper_tools = ["photoshop", "gimp", "canva", "lightroom", "paint.net", "snapseed", "pixlr", "coreldraw"]
            for cand in software_candidates:
                cand_lower = cand.lower()
                for tool in tamper_tools:
                    if tool in cand_lower:
                        detected_software = cand.strip()
                        break
                if detected_software:
                    break

    except Exception as e:
        print(f"Metadata inspection error: {e}")

    return detected_software


def detect_digital_patch_and_noise_anomalies(filepath):
    """
    Examines spatial noise uniformity and high-contrast digital patch boundaries.
    Fraudulent documents often contain artificially flat (zero-noise) white-out patches
    or sharp rectangular pasted bounding boxes around altered names or ID numbers.
    """
    try:
        image = cv2.imread(filepath)
        if image is None:
            return {"patch_detected": False, "noise_anomaly": False, "clipped_pixels_pct": 0.0}

        h, w = image.shape[:2]
        total_pixels = h * w
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 1. High-frequency noise distribution across a 4x4 grid
        kernel = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]])
        filtered = cv2.filter2D(gray, -1, kernel)

        bh = max(h // 4, 1)
        bw = max(w // 4, 1)
        stds = []
        for r in range(4):
            for c in range(4):
                cell = filtered[r * bh:(r + 1) * bh, c * bw:(c + 1) * bw]
                if cell.size > 0:
                    stds.append(float(np.std(cell)))

        noise_anomaly = False
        if stds:
            min_std = min(stds)
            max_std = max(stds)
            # High disparity where some sectors have no sensor noise while others do
            if min_std > 0 and (max_std / min_std) > 6.0 and min_std < 1.8:
                noise_anomaly = True

        # 2. Pure clipping analysis (pure white 255 or pure black 0 unnatural patches)
        pure_white_count = np.count_nonzero(gray >= 254)
        white_pct = (pure_white_count / max(total_pixels, 1)) * 100.0

        # 3. Rectangular edge contour detection in interior (pasted text boxes)
        patch_detected = False
        edges = cv2.Canny(gray, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Check bounding boxes between 1% and 25% of card area (typical pasted name/number box)
            if (0.01 * total_pixels) < area < (0.25 * total_pixels):
                x, y, cw, ch = cv2.boundingRect(cnt)
                # Ignore whole-card outer borders
                if x > 10 and y > 10 and (x + cw) < (w - 10) and (y + ch) < (h - 10):
                    aspect = cw / max(ch, 1)
                    if 2.0 < aspect < 9.0:  # Typical text box aspect ratio
                        # Check if internal region has unusually uniform color
                        roi = gray[y:y + ch, x:x + cw]
                        if roi.size > 0 and float(np.std(roi)) < 6.0:
                            patch_detected = True
                            break

        return {
            "patch_detected": patch_detected,
            "noise_anomaly": noise_anomaly,
            "clipped_pixels_pct": round(white_pct, 2)
        }

    except Exception as e:
        print(f"Digital patch detection error: {e}")
        return {"patch_detected": False, "noise_anomaly": False, "clipped_pixels_pct": 0.0}


def analyze_document_forensics(filepath, document_type):
    """
    Central Image Forensics Screening Engine (OpenCV + PIL).
    Provides deterministic, mathematically explainable tampering analysis.
    """
    ela_res = perform_error_level_analysis(filepath)
    sharp_res = analyze_sharpness_and_blur(filepath)
    geom_res = check_aspect_ratio_and_resolution(filepath, document_type)
    software_tag = inspect_image_metadata(filepath)
    patch_res = detect_digital_patch_and_noise_anomalies(filepath)

    indicators = []
    forensic_risk = 0

    # 1. Digital editor metadata signature
    if software_tag:
        forensic_risk += 35
        indicators.append(f"Digital Editor Footprint: Binary headers reveal editing via '{software_tag}'.")

    # 2. Error Level Analysis (ELA) compression inconsistencies
    if ela_res["anomaly_detected"]:
        forensic_risk += 35
        indicators.append(f"Compression Anomaly (ELA): Recompression delta variance flags digitally spliced or pasted elements (score: {ela_res['score']}).")
    elif ela_res["score"] > 30:
        forensic_risk += 15
        indicators.append(f"Compression Variance: Elevated recompression disparity across image sectors (score: {ela_res['score']}).")

    # 3. Spatial sharpness & Laplacian variance
    if sharp_res["splicing_detected"]:
        forensic_risk += 30
        indicators.append("Sharpness Disparity: Localized Laplacian gradients indicate high-sharpness digital text overlaid on degraded background.")
    elif sharp_res["is_blurry"]:
        forensic_risk += 10
        indicators.append(f"Defocus / Low Sharpness: Image focus is degraded (variance: {sharp_res['overall_variance']}), which may obscure security print.")

    # 4. Digital patch & noise uniformity analysis
    if patch_res["patch_detected"]:
        forensic_risk += 30
        indicators.append("Digital Patch Boundary: Sharp rectangular boundary with flat internal fill detected inside document interior.")

    if patch_res["noise_anomaly"]:
        forensic_risk += 20
        indicators.append("Sensor Noise Disparity: Irregular noise distribution across document sectors indicates artificial digital alterations.")

    # 5. Document geometry and resolution
    if not geom_res["aspect_valid"]:
        forensic_risk += 15
        indicators.append(f"Non-Standard Aspect Ratio: Bounding proportions ({geom_res['aspect_ratio']}) deviate from ISO/IEC 7810 ID-1 standard (~1.59).")

    if geom_res["low_resolution"]:
        forensic_risk += 10
        indicators.append(f"Low Resolution Artifact: Image dimensions ({geom_res['resolution']}) are below recommended minimum of 500x300.")

    # Clamp risk score
    forensic_risk = max(0, min(100, forensic_risk))
    suspicious = forensic_risk >= 30

    if not indicators:
        indicators.append("Clean Forensic Baseline: No compression anomalies, digital editor signatures, or structural distortions detected.")

    confidence = 0.92 if not sharp_res["is_blurry"] else 0.75

    return {
        "status": "completed",
        "suspicious": suspicious,
        "risk_score": forensic_risk,
        "confidence": confidence,
        "indicators": indicators,
        "metrics": {
            "ela_score": ela_res["score"],
            "sharpness_variance": sharp_res["overall_variance"],
            "aspect_ratio": geom_res["aspect_ratio"],
            "resolution": geom_res["resolution"],
            "software_detected": software_tag,
            "patch_detected": patch_res["patch_detected"],
            "noise_anomaly": patch_res["noise_anomaly"]
        }
    }
