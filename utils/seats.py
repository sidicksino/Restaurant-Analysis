import math

UP_STEP = 0.1     # how fast a seat's score climbs when someone is detected there
DOWN_STEP = 0.05  # how slowly a seat's score falls when no one is seen there


def seat_angle(seat, seat_count):
    # Seats are evenly spaced around the table in a circle.
    return (360 / seat_count) * seat


def angle_between(a, b):
    # The smallest angle between two directions, from 0 to 180 degrees.
    diff = abs(a - b) % 360
    return 360 - diff if diff > 180 else diff


def find_seats(table_center, seated, seat_count):
    # Matches each guest at the table to the closest available seat.
    #   table_center = (table_x, table_y) middle of the table top
    #   seated       = list of (x, y) center points of people at the table
    #   seat_count   = number of seats around the table
    table_x, table_y = table_center

    pairs = []
    for person, (x, y) in enumerate(seated):
        direction = math.degrees(math.atan2(y - table_y, x - table_x))
        for seat in range(seat_count):
            pairs.append((angle_between(direction, seat_angle(seat, seat_count)), person, seat))
    pairs.sort()

    taken = []
    seen_people = set()
    seen_seats = set()
    for diff, person, seat in pairs:
        if person not in seen_people and seat not in seen_seats:
            seen_people.add(person)
            seen_seats.add(seat)
            taken.append(seat)

    return taken


def steady_seats(scores, taken_now, guest_count):
    # Updates the seat scores and returns which seats are taken.
    #   scores      = list of confidence scores for each seat, updated in place
    #   taken_now   = seat indices found in the current frame
    #   guest_count = locked number of guests at the table
    for seat in range(len(scores)):
        if seat in taken_now:
            scores[seat] = min(1.0, scores[seat] + UP_STEP)
        else:
            scores[seat] = max(0.0, scores[seat] - DOWN_STEP)

    if guest_count <= 0:
        return [False] * len(scores)

    # Pick the guest_count seats with the highest scores
    best_seats = sorted(range(len(scores)), key=lambda s: scores[s], reverse=True)[:guest_count]
    return [s in best_seats for s in range(len(scores))]
