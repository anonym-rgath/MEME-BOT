from memebot.bot.handlers import clearchat_ids


def test_full_range_newest_first():
    ids = clearchat_ids(100, 100)
    assert ids == list(range(100, 0, -1))
    assert len(ids) == 100
    assert ids[0] == 100 and ids[-1] == 1


def test_clamped_at_chat_start():
    assert clearchat_ids(5, 100) == [5, 4, 3, 2, 1]


def test_respects_limit():
    ids = clearchat_ids(1000, 50)
    assert len(ids) == 50
    assert ids[0] == 1000
    assert ids[-1] == 951
