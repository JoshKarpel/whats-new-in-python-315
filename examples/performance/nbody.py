def nbody(steps):
    bodies = [
        [0.0, 0.0, 0.0, 0.01, 0.02, 0.0, 1.0],
        [1.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.001],
        [0.0, 2.0, 0.0, -0.3, 0.0, 0.0, 0.002],
        [3.0, 1.0, 0.5, 0.0, 0.1, 0.2, 0.0005],
    ]
    dt = 0.01
    for _ in range(steps):
        for i, bi in enumerate(bodies):
            for bj in bodies[i + 1 :]:
                dx, dy, dz = bi[0] - bj[0], bi[1] - bj[1], bi[2] - bj[2]
                d2 = dx * dx + dy * dy + dz * dz + 0.01
                mag = dt / (d2 * d2**0.5)
                bi[3] -= dx * bj[6] * mag
                bi[4] -= dy * bj[6] * mag
                bi[5] -= dz * bj[6] * mag
                bj[3] += dx * bi[6] * mag
                bj[4] += dy * bi[6] * mag
                bj[5] += dz * bi[6] * mag
        for b in bodies:
            b[0] += dt * b[3]
            b[1] += dt * b[4]
            b[2] += dt * b[5]
    return bodies[0][0]


if __name__ == "__main__":
    nbody(60_000)
