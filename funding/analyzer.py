def check_threshold(rate, threshold):
    if rate is None:
        return False
    return rate >= threshold
