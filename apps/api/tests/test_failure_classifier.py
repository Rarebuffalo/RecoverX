from app.services.failure_classifier import FailureClassifier


def test_failure_classification_transient():
    res1 = FailureClassifier.classify(failure_code="BAD_REQUEST_GATEWAY_TIMEOUT")
    assert res1.category == "TRANSIENT"
    assert res1.is_transient is True
    assert res1.is_permanent is False

    res2 = FailureClassifier.classify(failure_reason="Bank switch did not respond in time")
    assert res2.category == "TRANSIENT"


def test_failure_classification_customer_action():
    res1 = FailureClassifier.classify(failure_code="BAD_REQUEST_USER_CANCELLED")
    assert res1.category == "CUSTOMER_ACTION_REQUIRED"
    assert res1.is_customer_actionable is True

    res2 = FailureClassifier.classify(failure_reason="Customer dropped out of UPI app drawer")
    assert res2.category == "CUSTOMER_ACTION_REQUIRED"


def test_failure_classification_insufficient_funds():
    res = FailureClassifier.classify(failure_code="PAYMENT_CARD_INSUFFICIENT_FUNDS")
    assert res.category == "INSUFFICIENT_FUNDS"
    assert res.is_customer_actionable is True


def test_failure_classification_method_issue():
    res = FailureClassifier.classify(failure_code="PAYMENT_CARD_INVALID_CVV")
    assert res.category == "PAYMENT_METHOD_ISSUE"


def test_failure_classification_permanent():
    res1 = FailureClassifier.classify(failure_code="PAYMENT_CARD_STOLEN")
    assert res1.category == "PERMANENT"
    assert res1.is_permanent is True

    res2 = FailureClassifier.classify(failure_reason="Account frozen due to fraud investigation")
    assert res2.category == "PERMANENT"
    assert res2.is_permanent is True


def test_failure_classification_unknown():
    res = FailureClassifier.classify(failure_code="NON_STANDARD_CUSTOM_ERROR")
    assert res.category == "UNKNOWN"
    assert res.confidence == 0.50
