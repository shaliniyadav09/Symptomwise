import re
from django.core.exceptions import ValidationError

def validate_ten_digit_phone(value):
    """
    Validates that the phone number has exactly 10 digits.
    """
    # The 'value' from PhoneNumberField is an object, so convert it to a string
    phone_number = str(value)
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone_number)
    
    # Check if the remaining digits are exactly 10
    if len(digits) != 10:
        raise ValidationError("Phone number must be exactly 10 digits.")