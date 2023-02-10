from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

locationData = {
    "location": "New Testopolis",
    "coords": {
        "latitude": 54.6541971,
        "longitude": -5.6730648
    }
}


def test_update_location_successful(jwt_token):
    response = client.post(
        "/updateLocation",
        headers={"Authorization": "Bearer " + jwt_token},
        json=locationData)
    assert response.status_code == 200
    assert response.json() == "Successfully updated location"


def test_update_location_unsuccessful():
    response = client.post(
        "/updateLocation", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
