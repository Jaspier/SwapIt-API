from fastapi.testclient import TestClient

from main import app
from .conftest import mock_login

client = TestClient(app)

match = {
    "type": "match",
    "matchObj": {
        "loggedInProfile": {
            "active": False,
            "coords": {
                "latitude": 54.591379,
                "longitude": -5.69317
            },
            "displayName": "user@swiped.io",
            "id": "SomeRandomSwipedUserIdentifier",
            "itemName": "a nice item",
            "location": "wonderland",
            "photoUrls": '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
            "profilePic": "",
            "radius": 27,
            "timestamp": '2023-02-09T20:42:52.686000+00:00',
            "isNewUser": False,
        },
        "userSwiped": {
            "active": False,
            "coords": {
                "latitude": 54.6541971,
                "longitude": -5.6730648,
            },
            "displayName": "testuser",
            "id": "QQyOyOf4dLdAN8SD4f2t3JM4g0r1",
            "deviceToken": "ExponentPushToken[BtpUlRN8i23S_vhK7np6xH]",
            "itemName": "test item",
            "location": "Testopolis",
            "photoUrls": "[{\"uri\":\"e58470d6-10ce-48da-a681-92a4f32979fc.jpg\"}]",
            "radius": 30,
            "timestamp": "2023-02-09T20:42:52.686000+00:00"
        }
    }
}

message = {
    "type": "message",
    "messageObj": {
        "message": "Hello from test!",
        "receiverId": "QQyOyOf4dLdAN8SD4f2t3JM4g0r1",
        "sender": {
            "active": False,
            "coords": {
                "latitude": 54.591379,
                "longitude": -5.69317
            },
            "displayName": "user@swiped.io",
            "id": "SomeRandomSwipedUserIdentifier",
            "itemName": "a nice item",
            "location": "wonderland",
            "photoUrls": '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
            "profilePic": "",
            "radius": 27,
            "timestamp": "2023-02-09T20:42:52.686000+00:00"
        }
    }
}

expected_device_token_not_exists = {
    "status": "error",
    "message": '"ExponentPushToken[BtpUlRN8i23S_vhK7np6xH]" is not a registered push notification recipient'}


def test_send_push_notification_message_device_token_not_exists():
    token = mock_login("testuser@test.io", "test123")
    response = client.post(
        "/sendPushNotification",
        headers={"Authorization": "Bearer " + token},
        json=message)
    assert response.status_code == 200
    assert response.json() == expected_device_token_not_exists


def test_send_push_notification_match_device_token_not_exists():
    token = mock_login("testuser@test.io", "test123")
    response = client.post(
        "/sendPushNotification",
        headers={"Authorization": "Bearer " + token},
        json=match)
    assert response.status_code == 200
    assert response.json() == expected_device_token_not_exists


def test_send_push_notification_match_user_not_exists(jwt_token):
    match["matchObj"]["userSwiped"]["id"] = "NotExists"
    response = client.post(
        "/sendPushNotification",
        headers={"Authorization": "Bearer " + jwt_token},
        json=match)

    assert response.status_code == 400
    assert response.json() == "Matched user does not exist"


def test_send_push_notification_message_receiver_not_exists(jwt_token):
    message["messageObj"]["receiverId"] = "NotExists"
    response = client.post(
        "/sendPushNotification",
        headers={"Authorization": "Bearer " + jwt_token},
        json=message)

    assert response.status_code == 400
    assert response.json() == "Receiver does not exist"


def test_swipe_right_unsuccessful():
    response = client.post(
        "/sendPushNotification",
        headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
