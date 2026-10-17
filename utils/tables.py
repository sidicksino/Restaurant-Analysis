import cv2
import numpy as np

TINT = 0.4  # how strongly the color covers a table top, from 0 (not at all) to 1 (fully)


def people_at_table(points, centers):
    # How many people are at one table.
    #   points  = corner points of the area around the table (table plus chairs)
    #   centers = one (x, y) point for every person: the centre of their box
    # A person is at the table when their centre is inside the area.
    polygon = np.array(points, np.int32)
    return sum(cv2.pointPolygonTest(polygon, center, False) >= 0 for center in centers)


def draw_table_tops(frame, table_tops, colors):
    # Highlights every table top in its own color and returns the new frame.
    #   table_tops = table name -> corner points of the table top
    #   colors     = table name -> color as (blue, green, red)
    overlay = frame.copy()
    for name, points in table_tops.items():
        table_top = np.array(points, np.int32)
        cv2.fillPoly(overlay, [table_top], colors[name])
        cv2.polylines(frame, [table_top], True, colors[name], 2)

    # Blend the filled table tops into the frame so the tables look tinted, not covered.
    return cv2.addWeighted(overlay, TINT, frame, 1 - TINT, 0)