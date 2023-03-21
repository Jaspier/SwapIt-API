from main import db


def UpdateProfilePicInChatMessages(uid: str, key: str):
    # Update profile pic key in messages
    query = db.collection("matches").where(
        "usersMatched", "array_contains", uid)
    docs = query.stream()

    matches = []
    for doc in docs:
        matches.append(doc.id)

    # Iterate through the matches and get the relevant messages
    for match_id in matches:
        # Query the messages subcollection for messages with the provided userId
        query = db.collection("matches").document(
            match_id).collection("messages").where("userId", "==", uid)
        docs = query.stream()

        # Update the photoUrl field for each relevant message
        for doc in docs:
            message_ref = db.collection("matches").document(
                match_id).collection("messages").document(doc.id)
            message_ref.update({"photoUrl": key})
