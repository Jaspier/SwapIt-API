from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)

user_swiped = {
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
    "radius": 27,
    "timestamp": "2023-02-09T20:42:52.686000+00:00"
}

user_matched = {
    "active": False,
    "coords": {
        "latitude": 54.7173,
        "longitude": -6.2055
    },
    "displayName": "swiped user",
    "id": "pRZu4xbq35Q1vzQBwlPrcGZztqw2",
    "itemName": "swiped item",
    "location": "swipeland",
    "photoUrls": '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
    "radius": 30,
    "timestamp": "2023-02-09T20:42:52.686000+00:00"
}

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


def test_swipe_right():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/swipeRight",
        headers={"Authorization": "Bearer " + token},
        json=user_swiped)
    assert response.status_code == 200
    assert response.json() == "Successfully added Swipe"


def test_swipe_right_match():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/swipeRight",
        headers={"Authorization": "Bearer " + token},
        json=user_matched)

    assert response.status_code == 201
    expected_result = matched_user.copy()
    expected_result.pop("timestamp")
    response_dict = response.json()
    response_dict.pop("timestamp")
    assert response_dict == expected_result


def test_swipe_right_user_not_exists():
    token = mock_login("unknown@test.io", "unknown")
    response = client.post(
        "/swipeRight",
        headers={"Authorization": "Bearer " + token},
        json=user_swiped)

    assert response.status_code == 404
    assert response.json() == "User does not exist"


def test_swipe_right_unsuccessful():
    response = client.post(
        "/swipeRight",
        headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400