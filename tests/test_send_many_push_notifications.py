from fastapi.testclient import TestClient

from main import app, version

client = TestClient(app)


notification = {
    "type": "delete",
    "notifications": [
        {
            "receiverId": "QQyOyOf4dLdAN8SD4f2t3JM4g0r1",
            "sender": "testuser1"
        },
        {
            "receiverId": "pRZu4xbq35Q1vzQBwlPrcGZztqw2",
            "sender": "testuser1"
        }
    ]
}

expected = {
    'notified': ['QQyOyOf4dLdAN8SD4f2t3JM4g0r1'],
    'failedToNotify': ['pRZu4xbq35Q1vzQBwlPrcGZztqw2']
}


def test_send_many_push_notifications_delete(jwt_token):
    response = client.post(
        f"/{version}/send_many_push_notifications",
        headers={"Authorization": "Bearer " + jwt_token},
        json=notification)
    assert response.status_code == 200
    assert response.json() == expected
