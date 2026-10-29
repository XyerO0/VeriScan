from utils import verify_document


def test_pan_match():

    result = verify_document(
        "pan",
        "Rahul Kumar",
        "ABCDE1234F",
        "INCOME TAX DEPARTMENT Rahul Kumar PAN ABCDE1234F"
    )

    assert result["success"] is True

    assert result["document"]["number_match"] is True

    assert result["document"]["detected_number"] == "ABCDE1234F"


def test_pan_mismatch():

    result = verify_document(
        "pan",
        "Rahul Kumar",
        "AAAAA1111A",
        "INCOME TAX DEPARTMENT Rahul Kumar PAN ABCDE1234F"
    )

    assert result["success"] is True

    assert result["document"]["number_match"] is False


def test_pan_not_detected():

    result = verify_document(
        "pan",
        "Rahul Kumar",
        "ABCDE1234F",
        "INCOME TAX DEPARTMENT Rahul Kumar"
    )

    assert result["success"] is True

    assert result["document"]["detected_number"] is None

    assert result["document"]["number_match"] is False


def test_name_similarity():

    result = verify_document(
        "pan",
        "Rahul Kumar",
        "ABCDE1234F",
        "INCOME TAX DEPARTMENT Rahul Kumar PAN ABCDE1234F"
    )

    assert result["identity"]["name_similarity"] >= 85


def test_invalid_document_type():

    result = verify_document(
        "passport",
        "Rahul Kumar",
        "ABC123",
        "Some document text"
    )

    assert result["success"] is False


def test_wrong_name_identity_mismatch():
    """
    Test that a mismatched name triggers high risk and identity mismatch flag
    even when the document number matches.
    """
    from utils import calculate_combined_risk, get_combined_risk_level

    result = verify_document(
        "pan",
        "Vikram Singh",  # Wrong name
        "ABCDE1234F",
        "INCOME TAX DEPARTMENT Rahul Kumar PAN ABCDE1234F"
    )

    assert result["success"] is True
    assert result["document"]["number_match"] is True
    assert result["identity"]["name_similarity"] < 50
    assert result["identity"]["is_impersonation_risk"] is True

    combined_score = calculate_combined_risk(
        result["risk"]["score"],
        0,
        name_similarity=result["identity"]["name_similarity"],
        number_match=result["document"]["number_match"],
        format_valid=result["document"]["format_valid"]
    )
    final_level = get_combined_risk_level(combined_score)

    assert final_level == "High Risk"
    assert combined_score >= 70


def test_aadhaar_verhoeff_checksum():
    """
    Test that an invalid 12-digit Aadhaar number fails the Verhoeff checksum.
    """
    result = verify_document(
        "aadhaar",
        "Rahul Kumar",
        "123456789012",  # Dummy invalid sequence
        "Government of India Unique Identification Authority of India Rahul Kumar 1234 5678 9012"
    )

    assert result["success"] is True
    assert result["document"]["checksum_valid"] is False
    assert any("Aadhaar Checksum Failure" in ind for ind in result["document"]["indicators"])
