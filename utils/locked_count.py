from collections import Counter


def update_locked_count(locked, recent, up_frames):
    # Stage 1: Going up
    # Look at the newest seconds only (up_frames). Counter finds the count
    # that appears most often. If it is higher than current locked count, take it.
    recent_list = list(recent)
    steady = Counter(recent_list[-up_frames:]).most_common(1)[0][0]
    if steady > locked:
        return steady

    # Stage 2: Going down
    # Look at the whole history window. Only if the count never reached
    # the locked count during this entire time do we lower it.
    highest = max(recent)
    if highest < locked:
        return highest

    return locked
