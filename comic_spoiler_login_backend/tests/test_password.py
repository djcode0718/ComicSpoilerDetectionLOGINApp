from app import is_valid_password

def test_password_validator():
    assert is_valid_password('Qwerty@123')
    assert not is_valid_password('short')
    assert not is_valid_password('NoNumber!')
    assert not is_valid_password('nouppercase1!')
    assert not is_valid_password('NOLOWERCASE1!')
    assert not is_valid_password('NoSpecial123')