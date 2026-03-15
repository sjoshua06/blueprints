def compatibility_score(distance):

    score = 1 / (1 + distance)

    return round(score * 100, 2)