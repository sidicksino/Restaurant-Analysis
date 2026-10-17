THIGH_TO_TORSO = 0.4   # knees this far below the hips (compared to torso length) means standing
KNEE_CONFIDENCE = 0.5  # only trust the knees if YOLO is at least this sure about them
SAME_PERSON = 0.5      # two boxes that overlap at least this much belong to the same person

# Positions of the body points we need in YOLO's pose output (it returns 17 points per person).
LEFT_SHOULDER, RIGHT_SHOULDER = 5, 6
LEFT_HIP, RIGHT_HIP = 11, 12
LEFT_KNEE, RIGHT_KNEE = 13, 14


def is_standing(keypoints):
    # When you stand, your knees are far below your hips. When you sit, they are at about the same height.
    points = keypoints.xy[0].tolist()
    confidence = keypoints.conf[0].tolist()

    # Knees hidden (usually under a table): we cannot say the person is standing.
    if max(confidence[LEFT_KNEE], confidence[RIGHT_KNEE]) < KNEE_CONFIDENCE:
        return False

    shoulder_y = (points[LEFT_SHOULDER][1] + points[RIGHT_SHOULDER][1]) / 2
    hip_y = (points[LEFT_HIP][1] + points[RIGHT_HIP][1]) / 2
    knee_y = (points[LEFT_KNEE][1] + points[RIGHT_KNEE][1]) / 2

    torso = hip_y - shoulder_y  # shoulders down to hips
    thigh = knee_y - hip_y      # hips down to knees
    return torso > 0 and thigh > THIGH_TO_TORSO * torso


def shared_area(box_a, box_b):
    # How much two boxes overlap, from 0 (not at all) to 1 (the same box).
    # This is the area they share divided by the area they cover together.
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    width = min(ax2, bx2) - max(ax1, bx1)
    height = min(ay2, by2) - max(ay1, by1)
    if width <= 0 or height <= 0:
        return 0

    shared = width * height
    total = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - shared
    return shared / total


def remove_standing(boxes, pose_result):
    # Only sitting people can occupy a table. Waiters and people walking past are on their feet.
    #   boxes       = result.boxes of the model we use to find people
    #   pose_result = result of a YOLO pose model on the same frame (it tells us who is standing)
    # We drop every box that belongs to a person the pose model sees standing, and return the rest.
    # A person the pose model cannot see is treated as sitting.
    standing = []
    for box, keypoints in zip(pose_result.boxes, pose_result.keypoints):
        if is_standing(keypoints):
            standing.append(box.xyxy[0].tolist())

    sitting = []  # positions of the boxes we keep
    for i, corners in enumerate(boxes.xyxy.tolist()):
        if not any(shared_area(corners, other) >= SAME_PERSON for other in standing):
            sitting.append(i)
    return boxes[sitting]