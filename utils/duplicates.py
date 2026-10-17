MAX_OVERLAP = 0.7  # two boxes that overlap more than this are treated as the same person


def overlap(box_a, box_b):
    # How much of the smaller box is covered by the other box, from 0 (not at all) to 1 (fully).
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    width = min(ax2, bx2) - max(ax1, bx1)
    height = min(ay2, by2) - max(ay1, by1)
    if width <= 0 or height <= 0:
        return 0  # the boxes do not touch

    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return (width * height) / min(area_a, area_b)


def remove_duplicates(boxes):
    # YOLO sometimes puts two boxes on one person, for example one around the
    # upper body and one around the whole body. We go through the boxes from most
    # to least confident and keep a box only if it does not sit on top of one we already kept.

    # .tolist() turns YOLO's boxes into plain Python numbers. Comparing those is far
    # faster than comparing the GPU tensors YOLO returns.
    corners = boxes.xyxy.tolist()
    confidences = boxes.conf.tolist()
    order = sorted(range(len(corners)), key=lambda i: confidences[i], reverse=True)

    kept = []  # positions of the boxes we keep
    for i in order:
        if all(overlap(corners[i], corners[k]) < MAX_OVERLAP for k in kept):
            kept.append(i)
    return [boxes[i] for i in kept]