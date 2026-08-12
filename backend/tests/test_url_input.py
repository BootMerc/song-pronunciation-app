import pytest

from app.services.title_guess import guess_title_artist
from app.services.youtube_url import extract_video_id

VALID_ID = "fJ9rUzIMcZQ"


class TestExtractVideoId:
    @pytest.mark.parametrize(
        "url",
        [
            f"https://www.youtube.com/watch?v={VALID_ID}",
            f"https://youtube.com/watch?v={VALID_ID}&list=PLxx&index=3",
            f"https://youtu.be/{VALID_ID}",
            f"https://youtu.be/{VALID_ID}?t=42",
            f"https://m.youtube.com/watch?v={VALID_ID}",
            f"https://music.youtube.com/watch?v={VALID_ID}&feature=share",
            f"https://www.youtube.com/embed/{VALID_ID}",
            f"https://www.youtube.com/shorts/{VALID_ID}",
            f"www.youtube.com/watch?v={VALID_ID}",  # no scheme
            f"https://www.youtube-nocookie.com/embed/{VALID_ID}",
        ],
    )
    def test_valid_formats_extract_correctly(self, url):
        assert extract_video_id(url) == VALID_ID

    @pytest.mark.parametrize(
        "url",
        [
            "not a url at all",
            f"https://example.com/watch?v={VALID_ID}",  # wrong host
            "https://www.youtube.com/watch?v=short",  # invalid id length
            "",
            "   ",
            "https://www.youtube.com/",  # no video reference at all
        ],
    )
    def test_invalid_or_unrecognized_returns_none(self, url):
        assert extract_video_id(url) is None


class TestGuessTitleArtist:
    def test_standard_dash_format(self):
        title, artist = guess_title_artist(
            "Queen - Bohemian Rhapsody (Official Video)", "Queen Official"
        )
        assert title == "Bohemian Rhapsody"
        assert artist == "Queen"

    def test_bracketed_noise_stripped(self):
        title, artist = guess_title_artist(
            "Bruno Mars - Just The Way You Are [Official Music Video]", "Bruno Mars"
        )
        assert title == "Just The Way You Are"
        assert artist == "Bruno Mars"

    def test_pipe_suffix_stripped_without_leaving_orphan_pipe(self):
        # Regression: an earlier version ran the bare-noise-word regex
        # before the pipe-suffix regex, which stripped "Official Video"
        # out from under the pipe pattern and left a trailing "|".
        title, artist = guess_title_artist(
            "THE CHAINSMOKERS & COLDPLAY - Something Just Like This | Official Video",
            "Chainsmokers",
        )
        assert title == "Something Just Like This"
        assert "|" not in title

    def test_japanese_corner_bracket_convention(self):
        title, artist = guess_title_artist("YOASOBI「アイドル」Official Music Video", "YOASOBI")
        assert title == "アイドル"
        assert artist == "YOASOBI"

    def test_no_separator_falls_back_to_channel_name(self):
        title, artist = guess_title_artist("A Totally Unstructured Video Title", "Some Channel")
        assert artist == "Some Channel"
        assert title == "A Totally Unstructured Video Title"

    def test_channel_branding_suffix_stripped_in_fallback(self):
        _, artist = guess_title_artist("Unstructured Title With No Dash", "Adele VEVO")
        assert artist == "Adele"
