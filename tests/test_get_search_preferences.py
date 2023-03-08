from fastapi.testclient import TestClient

from main import app
from .conftest import mock_login

client = TestClient(app)

searchPreferences = {
    'coords': {
        'latitude': 54.6541971, 'longitude': -5.6730648
    },
    'passes': [],
    'radius': 30,
    'swipes': ['FlGdc4N4CyMAyKDfNJEHrcGGGRa2']
}


def test_get_search_preferences_successful():
    token = mock_login("testuser@test.io", "test123")
    response = client.get(
        "/getSearchPreferences", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json() == searchPreferences


def test_get_search_preferences_unsuccessful():
    response = client.get(
        "/getSearchPreferences", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
