"""Tests for Text-to-Speech (TTS) synthesis engine."""

from unittest.mock import AsyncMock, patch
import pytest
from igris.voice.tts import EdgeTTSClient, TTSConfig


def test_tts_config():
    """Verify TTS configuration parameters."""
    cfg = TTSConfig(voice="bn-BD-PradeepNeural", rate="+10%")
    assert cfg.voice == "bn-BD-PradeepNeural"
    assert cfg.rate == "+10%"


@pytest.mark.asyncio
async def test_edge_tts_empty_text():
    """Verify empty text produces empty bytes and succeeds without calling API."""
    client = EdgeTTSClient()
    audio = await client.synthesize("")
    assert audio == b""

    res = await client.speak("   ")
    assert res is True


@pytest.mark.asyncio
async def test_edge_tts_synthesize_mocked():
    """Verify synthesize in-memory streaming with mocked communicate."""
    client = EdgeTTSClient()

    fake_chunks = [
        {"type": "audio", "data": b"ID3fake_mp3_header"},
        {"type": "WordBoundary", "data": "dummy"},
        {"type": "audio", "data": b"_audio_payload"},
    ]

    async def fake_stream():
        for ch in fake_chunks:
            yield ch

    mock_comm = AsyncMock()
    mock_comm.stream = fake_stream

    with patch("edge_tts.Communicate", return_value=mock_comm):
        result_bytes = await client.synthesize("Hello Igris")
        assert result_bytes == b"ID3fake_mp3_header_audio_payload"

