from app.services.superlative_service import pick_winner_index


def test_clear_majority():
    assert pick_winner_index([1, 5, 2]) == 1


def test_no_votes_returns_none():
    assert pick_winner_index([0, 0, 0]) is None


def test_tie_breaks_among_tied_only():
    winner = pick_winner_index([3, 0, 3])
    assert winner in (0, 2)


def test_single_option_with_votes():
    assert pick_winner_index([4]) == 0
