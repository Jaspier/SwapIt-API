from fastapi.testclient import TestClient

from main import app, db
from .mock import mock_login

client = TestClient(app)

usersMatched = ["pRZu4xbq35Q1vzQBwlPrcGZztqw2", "FlGdc4N4CyMAyKDfNJEHrcGGGRa2"]

matched_user = {
    'active': False,
    'location': 'New Testopolis',
    'displayName': 'testuser1',
    'id': 'FlGdc4N4CyMAyKDfNJEHrcGGGRa2',
    'itemName': 'test1 item',
    'photoUrls': '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
    'timestamp': '2023-02-10T02:57:36.226000+00:00',
    'radius': 30,
    'coords': {'latitude': 54.6541971, 'longitude': -5.6730648},
    'profilePic': 'https://preview.redd.it/1eboxhg5jij51.jpg?auto=webp&s=907a4ff5366b6e50eaf2f9aa2b97f5a47e02c192'
}

matchDoc = {
    "timestamp": "2023-02-10T02:57:36.226000+00:00",
    "users": {
        "FlGdc4N4CyMAyKDfNJEHrcGGGRa2": {
            'active': False,
            'location': 'New Testopolis',
            'displayName': 'testuser1',
            'id': 'FlGdc4N4CyMAyKDfNJEHrcGGGRa2',
            'itemName': 'test1 item',
            'photoUrls': '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
            'timestamp': '2023-02-10T02:57:36.226000+00:00',
            'radius': 30,
            'coords': {'latitude': 54.6541971, 'longitude': -5.6730648},
            'profilePic': 'https://preview.redd.it/1eboxhg5jij51.jpg?auto=webp&s=907a4ff5366b6e50eaf2f9aa2b97f5a47e02c192'
        },
        "pRZu4xbq35Q1vzQBwlPrcGZztqw2": {
            'active': False,
            'location': 'swipe land',
            'displayName': 'swiped user',
            'id': 'pRZu4xbq35Q1vzQBwlPrcGZztqw2',
            'isNewUser': False,
            'itemName': 'swiped item',
            'photoUrls': '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
            'timestamp': '2023-02-10T02:57:36.226000+00:00',
            'radius': 30,
            'coords': {'latitude': 54.7173, 'longitude': -6.2055},
            'profilePic': None
        }
    }
}


def test_delete_match_successful():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/deleteMatch",
        headers={"Authorization": "Bearer " + token},
        json=usersMatched)
    assert response.status_code == 204
    assert response.json() == "Successfully delete match"

    # add swipe back
    db.collection(u'users').document('pRZu4xbq35Q1vzQBwlPrcGZztqw2').collection(
        u'swipes').document(matched_user['id']).set(matched_user)

    # create match again
    db.collection(u'matches').document(
        "pRZu4xbq35Q1vzQBwlPrcGZztqw2FlGdc4N4CyMAyKDfNJEHrcGGGRa2").set(matchDoc)


def test_delete_match_unsuccessful():
    response = client.post(
        "/deleteMatch", headers={"Authorization": "Bearer fail"},
        json=usersMatched)
    assert response.status_code == 400
