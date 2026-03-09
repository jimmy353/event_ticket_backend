import requests


def send_expo_push(tokens, title, body, data=None):
    """
    Send push notification using Expo Push API

    tokens: list of Expo push tokens
    title: notification title
    body: notification message
    data: optional navigation data
    """

    if not tokens:
        return {"error": "No tokens provided"}

    messages = []

    for token in tokens:
        messages.append({
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
            "priority": "high",
            "channelId": "default",
            "data": data or {}
        })

    try:

        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            json=messages,
            headers={
                "Content-Type": "application/json"
            }
        )

        return response.json()

    except Exception as e:
        return {"error": str(e)}