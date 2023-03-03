from fastapi.testclient import TestClient

from main import app
from .conftest import mock_login

client = TestClient(app)

notification = {
    "type": "message",
    "matchDetails": {
        "id": "QQyOyOf4dLdAN8SD4f2t3JM4g0r1FlGdc4N4CyMAyKDfNJEHrcGGGRa2",
        "timestamp": "2023-02-09T20:42:52.686000+00:00",
        "users": {
            "FlGdc4N4CyMAyKDfNJEHrcGGGRa2": {
                "active": False,
                "coords": {
                    "latitude": 54.6541971,
                    "longitude": -5.6730648
                },
                "displayName": "testuser1",
                "id": "FlGdc4N4CyMAyKDfNJEHrcGGGRa2",
                "itemName": "test1 item",
                "location": "New Testopolis",
                "photoUrls": "[{\"uri\":\"e58470d6-10ce-48da-a681-92a4f32979fc.jpg\"}]",
                "profilePic": "https://preview.redd.it/1eboxhg5jij51.jpg?auto=webp&s=907a4ff5366b6e50eaf2f9aa2b97f5a47e02c192",
                "radius": 30,
                "timestamp": "2023-02-09T20:42:52.686000+00:00"
            },
            "QQyOyOf4dLdAN8SD4f2t3JM4g0r1": {
                "active": False,
                "coords": {
                    "latitude": 54.6541971,
                    "longitude": -5.6730648
                },
                "displayName": "testuser",
                "id": "QQyOyOf4dLdAN8SD4f2t3JM4g0r1",
                "itemName": "test item",
                "location": "Testopolis",
                "photoUrls": "[{\"uri\":\"e58470d6-10ce-48da-a681-92a4f32979fc.jpg\"}]",
                "profilePic": "",
                "radius": 30,
                "timestamp": "2023-02-09T20:42:52.686000+00:00"
            }
        },
        "usersMatched": ["QQyOyOf4dLdAN8SD4f2t3JM4g0r1", "FlGdc4N4CyMAyKDfNJEHrcGGGRa2"],
        "deactivated": False
    },
    "message": "test"
}

expected_device_token_not_exists = {
    "status": "error",
    "message": '"ExponentPushToken[BtpUlRN8i23S_vhK7np6xH]" is not a registered push notification recipient'}


def test_send_push_notification_message_device_token_not_exists(jwt_token):
    response = client.post(
        "/sendPushNotification",
        headers={"Authorization": "Bearer " + jwt_token},
        json=notification)
    assert response.status_code == 200
    assert response.json() == expected_device_token_not_exists


def test_send_push_notification_match_device_token_not_exists(jwt_token):
    notification["type"] = "match"
    response = client.post(
        "/sendPushNotification",
        headers={"Authorization": "Bearer " + jwt_token},
        json=notification)
    assert response.status_code == 200
    assert response.json() == expected_device_token_not_exists


def test_send_push_notification_receiver_not_exists(jwt_token):
    notification["matchDetails"]["users"]["QQyOyOf4dLdAN8SD4f2t3JM4g0r1"]["id"] = "NotExists"
    notification["type"] = "message"
    response = client.post(
        "/sendPushNotification",
        headers={"Authorization": "Bearer " + jwt_token},
        json=notification)

    assert response.status_code == 400
    assert response.json() == "Receiver does not exist"


def test_swipe_right_unsuccessful():
    response = client.post(
        "/sendPushNotification",
        headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
