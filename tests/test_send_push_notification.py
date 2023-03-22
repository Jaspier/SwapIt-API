from fastapi.testclient import TestClient

from main import app, db, version
from firebase_admin import firestore

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

# Only testing unregistered token for now as I don't have access to dummy device
expected_device_token_error = {
    "status": "error",
    "message": '"ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]" is not a registered push notification recipient'}


def test_send_push_notification_message(jwt_token):
    response = client.post(
        f"/{version}/send_push_notification",
        headers={"Authorization": "Bearer " + jwt_token},
        json=notification)
    assert response.status_code == 200
    assert response.json() == expected_device_token_error


def test_send_push_notification_match(jwt_token):
    notification["type"] = "match"
    response = client.post(
        f"/{version}/send_push_notification",
        headers={"Authorization": "Bearer " + jwt_token},
        json=notification)
    assert response.status_code == 200
    assert response.json() == expected_device_token_error


def test_send_push_notification_receiver_device_token_not_exists(jwt_token):
    db.collection("users").document("QQyOyOf4dLdAN8SD4f2t3JM4g0r1").update({
        u'deviceToken': firestore.DELETE_FIELD
    })
    response = client.post(
        f"/{version}/send_push_notification",
        headers={"Authorization": "Bearer " + jwt_token},
        json=notification)

    assert response.status_code == 400
    assert response.json() == "Receiver QQyOyOf4dLdAN8SD4f2t3JM4g0r1 device token does not exist"

    db.collection("users").document("QQyOyOf4dLdAN8SD4f2t3JM4g0r1").update({
        u'deviceToken': "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
    })


def test_send_push_notification_unsuccessful():
    response = client.post(
        f"/{version}/send_push_notification",
        headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
