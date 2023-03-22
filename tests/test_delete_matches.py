from fastapi.testclient import TestClient
from main import app, db, version

client = TestClient(app)

logged_in_user = {
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

swap_partner_to_be_deleted = {
    'active': False,
    'location': 'Testopolis',
    'displayName': 'testuser',
    'id': 'QQyOyOf4dLdAN8SD4f2t3JM4g0r1',
    'isNewUser': False,
    'itemName': 'test item',
    'photoUrls': '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
    'timestamp': '2023-02-10T02:57:36.226000+00:00',
    'radius': 30,
    'coords': {'latitude': 54.6541971, 'longitude': -5.6730648},
    'profilePic': None
}

match_for_swap = {
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
    },
    "usersMatched": ["pRZu4xbq35Q1vzQBwlPrcGZztqw2", "FlGdc4N4CyMAyKDfNJEHrcGGGRa2"]
}

match_to_be_deleted = {
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
        "QQyOyOf4dLdAN8SD4f2t3JM4g0r1": {
            'active': False,
            'location': 'Testopolis',
            'displayName': 'testuser',
            'id': 'QQyOyOf4dLdAN8SD4f2t3JM4g0r1',
            'isNewUser': False,
            'itemName': 'test item',
            'photoUrls': '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
            'timestamp': '2023-02-10T02:57:36.226000+00:00',
            'radius': 30,
            'coords': {'latitude': 54.6541971, 'longitude': -5.6730648},
            'profilePic': None
        }
    },
    "usersMatched": ["QQyOyOf4dLdAN8SD4f2t3JM4g0r1", "FlGdc4N4CyMAyKDfNJEHrcGGGRa2"]
}

payload = {
    "itemName": "test1 item",
    "matchedUserId": "pRZu4xbq35Q1vzQBwlPrcGZztqw2"
}

expected = {
    'notifications':
    [
        {'receiverId': 'QQyOyOf4dLdAN8SD4f2t3JM4g0r1', 'sender': 'testuser1'}
    ],
    'type': 'delete'
}


def test_delete_matches_successful(jwt_token):
    response = client.post(
        f"/{version}/delete_matches",
        headers={"Authorization": "Bearer " + jwt_token},
        json=payload)
    assert response.status_code == 200
    assert response.json() == expected


def test_delete_matches_unsuccessful():
    # reset swipes
    db.collection(u'users').document('pRZu4xbq35Q1vzQBwlPrcGZztqw2').collection(
        u'swipes').document(logged_in_user['id']).set(logged_in_user)

    db.collection(u'users').document('QQyOyOf4dLdAN8SD4f2t3JM4g0r1').collection(
        u'swipes').document(logged_in_user['id']).set(logged_in_user)

    db.collection(u'users').document('FlGdc4N4CyMAyKDfNJEHrcGGGRa2').collection(
        u'swipes').document(swap_partner_to_be_deleted['id']).set(swap_partner_to_be_deleted)

    # reset matches
    db.collection(u'matches').document(
        "pRZu4xbq35Q1vzQBwlPrcGZztqw2FlGdc4N4CyMAyKDfNJEHrcGGGRa2").set(match_for_swap)

    db.collection(u'matches').document(
        "QQyOyOf4dLdAN8SD4f2t3JM4g0r1FlGdc4N4CyMAyKDfNJEHrcGGGRa2").set(match_to_be_deleted)
    response = client.post(
        f"/{version}/delete_matches", headers={"Authorization": "Bearer fail"},
        json=payload)
    assert response.status_code == 400
