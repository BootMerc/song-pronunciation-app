from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services import translation


def _response(status, body):
    return httpx.Response(status, json=body, request=httpx.Request("POST", "https://x.test"))


CLAUDE_OK = {"content": [{"type": "text", "text": '["I love you", "You are my everything"]'}]}
CLAUDE_WITH_FENCE = {"content": [{"type": "text", "text": '```json\n["hello", "world"]\n```'}]}
CLAUDE_WRONG_COUNT = {"content": [{"type": "text", "text": '["only one"]'}]}
CLAUDE_NOT_JSON = {"content": [{"type": "text", "text": "Sure, here are the translations: I love you"}]}


class TestTranslateLines:
    async def test_happy_path(self):
        with patch.object(translation.settings, "anthropic_api_key", "fake"):
            with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_response(200, CLAUDE_OK))):
                result = await translation.translate_lines(["line one", "line two"])
        assert result == ["I love you", "You are my everything"]

    async def test_blank_lines_preserved_without_being_sent_to_the_model(self):
        # Handled deterministically rather than trusting the model to
        # follow a "return empty for blank input" instruction — a
        # misaligned translation would be worse than none at all.
        with patch.object(translation.settings, "anthropic_api_key", "fake"):
            with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_response(200, CLAUDE_OK))) as post:
                result = await translation.translate_lines(["line one", "", "line two"])
        assert result == ["I love you", "", "You are my everything"]
        sent_prompt = post.call_args.kwargs["json"]["messages"][0]["content"]
        assert "1. line one" in sent_prompt and "2. line two" in sent_prompt
        assert "3." not in sent_prompt  # the blank line never became a third numbered entry

    async def test_all_blank_input_skips_the_api_call_entirely(self):
        with patch.object(translation.settings, "anthropic_api_key", "fake"):
            with patch("httpx.AsyncClient.post", new=AsyncMock()) as post:
                result = await translation.translate_lines(["", "", ""])
        assert result == ["", "", ""]
        assert not post.called

    async def test_markdown_code_fence_stripped(self):
        with patch.object(translation.settings, "anthropic_api_key", "fake"):
            with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_response(200, CLAUDE_WITH_FENCE))):
                result = await translation.translate_lines(["a", "b"])
        assert result == ["hello", "world"]

    async def test_wrong_translation_count_raises_rather_than_misaligning(self):
        with patch.object(translation.settings, "anthropic_api_key", "fake"):
            with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_response(200, CLAUDE_WRONG_COUNT))):
                with pytest.raises(translation.TranslationAPIError):
                    await translation.translate_lines(["a", "b"])

    async def test_non_json_response_raises(self):
        with patch.object(translation.settings, "anthropic_api_key", "fake"):
            with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_response(200, CLAUDE_NOT_JSON))):
                with pytest.raises(translation.TranslationAPIError):
                    await translation.translate_lines(["a"])

    async def test_missing_api_key_raises_config_error(self):
        with patch.object(translation.settings, "anthropic_api_key", ""):
            with pytest.raises(translation.TranslationConfigError):
                await translation.translate_lines(["a"])

    async def test_network_failure_wrapped_in_api_error(self):
        with patch.object(translation.settings, "anthropic_api_key", "fake"):
            with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=httpx.ConnectError("boom"))):
                with pytest.raises(translation.TranslationAPIError):
                    await translation.translate_lines(["a"])
