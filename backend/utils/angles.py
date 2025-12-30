# backend/utils/angles.py
import math
from typing import Sequence, Optional


def angle_3pts(
    a: Sequence[float],
    b: Sequence[float],
    c: Sequence[float],
) -> Optional[float]:
    """
    Compute the angle at point b (in degrees) formed by points a-b-c.

    Parameters
    ----------
    a, b, c : (x, y) or (x, y, z)
        Coordinates of the three points.

    Returns
    -------
    angle : float or None
        Angle in degrees at point b, or None if cannot be computed.
    """
    if len(a) < 2 or len(b) < 2 or len(c) < 2:
        return None

    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    cx, cy = c[0], c[1]

    # Vectors BA and BC
    ba = (ax - bx, ay - by)
    bc = (cx - bx, cy - by)

    # Magnitudes
    mag_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)

    if mag_ba == 0 or mag_bc == 0:
        return None

    # Dot product
    dot = ba[0] * bc[0] + ba[1] * bc[1]

    # Clamp to [-1,1] to avoid numeric issues
    cos_angle = max(min(dot / (mag_ba * mag_bc), 1.0), -1.0)

    angle = math.degrees(math.acos(cos_angle))
    return angle
