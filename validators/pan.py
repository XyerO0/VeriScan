import re

# =========================================================
# Income Tax Department (ITD) PAN Specifications
# 4th Character = Entity Type
# 5th Character = First letter of Surname/Last Name (for Individual 'P')
# =========================================================

PAN_ENTITY_MAP = {
    "P": "Individual",
    "C": "Company",
    "H": "Hindu Undivided Family (HUF)",
    "F": "Firm / Limited Liability Partnership",
    "A": "Association of Persons (AOP)",
    "T": "Trust",
    "B": "Body of Individuals (BOI)",
    "L": "Local Authority",
    "J": "Artificial Juridical Person",
    "G": "Government Agency"
}


def extract_pan(text):
    if not text:
        return None

    pattern = r"[A-Z]{5}[0-9]{4}[A-Z]"
    match = re.search(pattern, text.upper())

    if match:
        return match.group()

    return None


def validate_pan(user_pan, extracted_pan):
    if not extracted_pan:
        return "PAN not detected"

    if not user_pan:
        return "PAN not entered"

    if extracted_pan.upper() == user_pan.upper():
        return "PAN matches"

    return "PAN mismatch"


def validate_pan_format(pan):
    if not pan:
        return False

    pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
    return bool(re.fullmatch(pattern, pan.upper()))


def validate_pan_entity(pan):
    """
    Check if the 4th character of PAN is a valid entity type recognized by ITD.
    """
    if not pan or len(pan) < 4:
        return False, "Unknown"

    entity_code = pan[3].upper()
    entity_desc = PAN_ENTITY_MAP.get(entity_code)
    if entity_desc:
        return True, entity_desc

    return False, f"Invalid entity code '{entity_code}'"


def validate_pan_surname(pan, name):
    """
    For Individual PAN cards ('P' at 4th position), the 5th character
    must match the initial of the cardholder's last name (surname).
    """
    if not pan or len(pan) < 5 or not name:
        return None

    clean_pan = pan.upper()
    if clean_pan[3] != "P":
        # Only individuals have surname binding
        return True

    words = [w for w in name.strip().split() if w]
    if not words:
        return None

    # Last word represents the surname; for single-word names, use the word itself
    surname = words[-1].upper()
    expected_char = surname[0]
    actual_char = clean_pan[4]

    return actual_char == expected_char
