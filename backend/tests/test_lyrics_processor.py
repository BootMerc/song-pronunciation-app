from app.services.lyrics_processor import process_plain_lyrics, process_synced_lyrics


class TestProcessPlainLyrics:
    def test_multiple_lines_each_processed(self):
        lines = process_plain_lyrics("愛してる\n我爱你")
        assert len(lines) == 2
        assert lines[0].romanized == "Aishiteru"
        assert lines[1].romanized == "wǒ ài nǐ"

    def test_blank_lines_preserved_as_blank_not_dropped(self):
        # Verse/chorus separation in real lyrics depends on blank lines
        # surviving — dropping them would collapse the structure.
        lines = process_plain_lyrics("Line one\n\nLine two")
        assert len(lines) == 3
        assert lines[1].original == ""

    def test_none_of_the_lines_have_a_timestamp(self):
        lines = process_plain_lyrics("Some lyrics\nMore lyrics")
        assert all(line.timestamp_ms is None for line in lines)

    def test_unsupported_language_line_degrades_gracefully(self):
        # Hebrew has no transliteration module — must not raise and take
        # down the whole song, and must not silently show wrong output.
        lines = process_plain_lyrics("אני אוהב אותך")
        assert len(lines) == 1
        assert lines[0].supported is False
        assert lines[0].language == "he"
        assert lines[0].original == lines[0].romanized == lines[0].friendly

    def test_mixed_supported_and_unsupported_lines_in_one_song(self):
        lines = process_plain_lyrics("愛してる\nאני אוהב אותך\n我爱你")
        assert lines[0].supported is True
        assert lines[1].supported is False
        assert lines[2].supported is True

    def test_empty_input_produces_no_lines(self):
        assert process_plain_lyrics("") == []

    def test_malformed_input_with_stray_control_characters_does_not_crash(self):
        # Pasted lyrics can carry all sorts of copy-paste noise — the
        # pipeline must degrade a line, never throw an unhandled
        # exception that kills the whole request.
        lines = process_plain_lyrics("Normal line\n\x00\x01weird bytes\nAnother normal line")
        assert len(lines) == 3

    def test_extremely_long_line_does_not_crash(self):
        lines = process_plain_lyrics("あ" * 5000)
        assert len(lines) == 1


class TestProcessSyncedLyrics:
    def test_lrc_lines_carry_their_timestamps_through(self):
        lrc = "[00:00.00] 愛してる\n[00:04.00] 君のこと"
        lines = process_synced_lyrics(lrc)
        assert lines[0].timestamp_ms == 0
        assert lines[0].romanized == "Aishiteru"
        assert lines[1].timestamp_ms == 4000
        assert lines[1].romanized == "Kimi no koto"

    def test_lrc_metadata_tags_do_not_become_lyric_lines(self):
        lrc = "[ar:Artist]\n[ti:Title]\n[00:01.00] Actual lyric"
        lines = process_synced_lyrics(lrc)
        assert len(lines) == 1
        assert lines[0].original == "Actual lyric"

    def test_malformed_lrc_does_not_crash_the_whole_song(self):
        lrc = "garbage line with no timestamp\n[00:02.00] valid line\nmore garbage"
        lines = process_synced_lyrics(lrc)
        assert len(lines) == 1
        assert lines[0].original == "valid line"
