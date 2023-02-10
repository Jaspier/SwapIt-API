from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

message = {
    u'matchId': "pRZu4xbq35Q1vzQBwlPrcGZztqw2FlGdc4N4CyMAyKDfNJEHrcGGGRa2",
    u'message': "Test Message",
}


def test_send_message_successful(jwt_token):
    response = client.post(
        "/sendMessage",
        headers={"Authorization": "Bearer " + jwt_token},
        json=message)
    assert response.status_code == 200
    assert response.json() == "Successfully sent message"


def test_send_message_unsuccessful():
    response = client.post(
        "/sendMessage", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
