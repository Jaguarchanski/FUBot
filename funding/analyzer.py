from config import FREE_PLAN_THRESHOLD

def filter_funding(user, funding_list):
    filtered = []
    for f in funding_list:
        if user.plan == "free":
            if f["rate"] <= FREE_PLAN_THRESHOLD:
                filtered.append(f)
            else:
                filtered.append({"symbol": "hidden", "rate": f["rate"]})
        else:
            filtered.append(f)
    return filtered
