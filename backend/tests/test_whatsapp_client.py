import pytest

from acc_nomad.services.whatsapp_client import WhatsAppError, normalize_whatsapp_number


def test_normalize_with_ddi():
    assert normalize_whatsapp_number("5511999999999") == "5511999999999"


def test_normalize_local_mobile():
    assert normalize_whatsapp_number("(11) 99999-9999") == "5511999999999"


def test_normalize_local_landline():
    assert normalize_whatsapp_number("1133334444") == "551133334444"


def test_normalize_invalid():
    with pytest.raises(WhatsAppError):
        normalize_whatsapp_number("123")
