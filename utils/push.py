import requests


def send_expo_push(tokens, title, body):
    messages = []

    for token in tokens:
        messages.append({
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
        })

    response = requests.post(
        "https://exp.host/--/api/v2/push/send",
        json=messages,
        headers={"Content-Type": "application/json"}
    )

    return response.json()