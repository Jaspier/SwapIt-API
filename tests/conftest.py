import pytest
from main import pb


def mock_login(email: str, password: str):
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        jwt = user['idToken']
        return jwt
    except Exception:
        return None


@pytest.fixture(scope="session")
def jwt_token():
    email = "testuser1@test.io"
    password = "test123"
    jwt = mock_login(email, password)
    return jwt
