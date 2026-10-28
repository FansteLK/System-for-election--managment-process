"""Election result calculations."""


def dhondt(votes_by_poll, seats, census_percent):
    """Allocate `seats` with the D'Hondt method.

    votes_by_poll: {poll_number: vote_count}. Lists with no more than
    `census_percent` of all votes get no seats. Ties go to the list with
    more votes overall, then to the lower poll number.
    Returns {poll_number: seats} for every list in the input.
    """
    total = sum(votes_by_poll.values())
    allocation = {poll: 0 for poll in votes_by_poll}
    threshold = census_percent / 100 * total
    eligible = [poll for poll, count in votes_by_poll.items() if count > threshold]
    if not eligible:
        return allocation
    for _ in range(seats):
        winner = max(
            eligible,
            key=lambda p: (votes_by_poll[p] / (allocation[p] + 1), votes_by_poll[p], -p),
        )
        allocation[winner] += 1
    return allocation


def vote_shares(votes_by_poll, total_valid):
    """Share of valid votes per poll number, rounded to two decimals."""
    if total_valid == 0:
        return {poll: 0 for poll in votes_by_poll}
    return {poll: round(count / total_valid, 2) for poll, count in votes_by_poll.items()}
