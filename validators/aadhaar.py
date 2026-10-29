import re

# =========================================================
# Verhoeff Multiplication & Permutation Matrices
# Official UIDAI Aadhaar 12th Digit Checksum Algorithm
# =========================================================

VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]

VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]


def validate_verhoeff_checksum(aadhaar):
    """
    Validate 12-digit Aadhaar number against the official Verhoeff checksum algorithm.
    Detects single-digit errors and digit transposition typos.
    """
    if not aadhaar:
        return False

    clean_aadhaar = str(aadhaar).replace(" ", "").strip()
    if not clean_aadhaar.isdigit() or len(clean_aadhaar) != 12:
        return False

    # UIDAI Aadhaar cannot start with 0 or 1
    if clean_aadhaar[0] in ['0', '1']:
        return False

    c = 0
    reversed_num = clean_aadhaar[::-1]
    for i, digit in enumerate(reversed_num):
        c = VERHOEFF_D[c][VERHOEFF_P[i % 8][int(digit)]]

    return c == 0


def extract_aadhaar(text):
    if not text:
        return None

    pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
    match = re.search(pattern, text)

    if match:
        aadhaar = match.group()
        aadhaar = aadhaar.replace(" ", "")
        return aadhaar

    return None


def validate_aadhaar(user_aadhaar, extracted_aadhaar):
    if not extracted_aadhaar:
        return "Aadhaar not detected"

    if not user_aadhaar:
        return "Aadhaar not entered"

    user_aadhaar = user_aadhaar.replace(" ", "")

    if extracted_aadhaar == user_aadhaar:
        return "Aadhaar matches"

    return "Aadhaar mismatch"


def validate_aadhaar_format(aadhaar):
    if not aadhaar:
        return False

    pattern = r"^\d{12}$"
    clean_aadhaar = aadhaar.replace(" ", "")
    return bool(re.fullmatch(pattern, clean_aadhaar))
