from storage import get_users

def filter_alerts(funding_data):
    alerts = []
    for chat_id, data in get_users().items():
        threshold = data["threshold"]
        for ex, rate in funding_data.items():
            if abs(rate) >= threshold / 100:
                alerts.append((chat_id, ex, rate))
    return alerts
