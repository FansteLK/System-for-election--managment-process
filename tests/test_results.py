from election.admin.results import dhondt, vote_shares


def test_dhondt_textbook_example():
    # Classic example: 8 seats, parties A-D with 100k/80k/30k/20k votes.
    votes = {1: 100_000, 2: 80_000, 3: 30_000, 4: 20_000}
    assert dhondt(votes, seats=8, census_percent=0) == {1: 4, 2: 3, 3: 1, 4: 0}


def test_dhondt_applies_census():
    # Party 3 has 4% of votes, below the 5% threshold.
    votes = {1: 600, 2: 360, 3: 40}
    result = dhondt(votes, seats=10, census_percent=5)
    assert result[3] == 0
    assert sum(result.values()) == 10


def test_dhondt_allocates_all_seats():
    votes = {1: 1234, 2: 999, 3: 777, 4: 555}
    assert sum(dhondt(votes, seats=250, census_percent=5).values()) == 250


def test_dhondt_no_list_passes_census():
    assert dhondt({1: 0, 2: 0}, seats=250, census_percent=5) == {1: 0, 2: 0}


def test_vote_shares():
    assert vote_shares({1: 2, 2: 1, 3: 0}, 3) == {1: 0.67, 2: 0.33, 3: 0}
    assert vote_shares({1: 0, 2: 0}, 0) == {1: 0, 2: 0}
