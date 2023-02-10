from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_remove_profile_pic_successful(jwt_token):
    response = client.get(
        "/removeProfilePic", headers={"Authorization": "Bearer " + jwt_token})
    assert response.status_code == 204
    assert response.json() == "Successfully removed profile picture"


def test_remove_profile_pic_unsuccessful():
    response = client.get(
        "/removeProfilePic", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
