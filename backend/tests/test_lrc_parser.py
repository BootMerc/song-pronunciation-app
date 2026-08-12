from app.services.lrc_parser import parse_lrc


def test_basic_timestamped_lines():
    lrc = "[00:00.00] Listen to the wind blow\n[00:04.50] Watch the sun rise"
    result = parse_lrc(lrc)
    assert result == [(0, "Listen to the wind blow"), (4500, "Watch the sun rise")]


def test_metadata_tags_are_skipped_not_treated_as_lyric_lines():
    lrc = "[ar:Fleetwood Mac]\n[ti:The Chain]\n[length:04:31]\n[00:12.00] Run in the shadows"
    result = parse_lrc(lrc)
    assert result == [(12000, "Run in the shadows")]


def test_empty_line_at_a_timestamp_is_preserved_not_dropped():
    # Represents an instrumental gap — meaningfully different from "no
    # line here at all", so it must survive parsing.
    lrc = "[00:09.20]"
    assert parse_lrc(lrc) == [(9200, "")]


def test_minutes_over_59_handled_correctly():
    lrc = "[75:03.00] a very long song"
    assert parse_lrc(lrc) == [(4503000, "a very long song")]


def test_timestamp_without_fractional_seconds():
    lrc = "[01:30] no decimal here"
    assert parse_lrc(lrc) == [(90000, "no decimal here")]


def test_malformed_line_is_skipped_not_crashed_on():
    lrc = "this is not a valid LRC line at all\n[00:05.00] but this one is"
    assert parse_lrc(lrc) == [(5000, "but this one is")]


def test_empty_input():
    assert parse_lrc("") == []


def test_whitespace_around_brackets_tolerated():
    lrc = "   [00:01.00]   padded line   "
    assert parse_lrc(lrc) == [(1000, "padded line")]
