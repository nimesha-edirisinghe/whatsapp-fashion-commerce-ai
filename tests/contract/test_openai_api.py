"""Contract tests for OpenAI API."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestOpenAIEmbeddings:
    """Test OpenAI embeddings API contract."""

    @pytest.mark.asyncio
    async def test_create_embedding_returns_vector(self) -> None:
        """Test that create_embedding returns correct dimension vector."""
        from app.core.openai_client import create_embedding

        mock_embedding = [0.1] * 1536  # text-embedding-3-small dimension

        with patch("app.core.openai_client.openai_client") as mock_client:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=mock_embedding)]
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)

            result = await create_embedding("test text")

            assert len(result) == 1536
            assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_create_embedding_calls_correct_model(self) -> None:
        """Test that create_embedding uses text-embedding-3-small model."""
        from app.core.openai_client import create_embedding

        with patch("app.core.openai_client.openai_client") as mock_client:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)

            await create_embedding("test text")

            mock_client.embeddings.create.assert_called_once()
            call_args = mock_client.embeddings.create.call_args
            assert call_args.kwargs["model"] == "text-embedding-3-small"


class TestOpenAICompletion:
    """Test OpenAI chat completion API contract."""

    @pytest.mark.asyncio
    async def test_generate_response_returns_string(self) -> None:
        """Test that generate_response returns string content."""
        from app.core.openai_client import generate_response

        with patch("app.core.openai_client.openai_client") as mock_client:
            mock_choice = MagicMock()
            mock_choice.message.content = "Test response"
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            messages = [{"role": "user", "content": "Hello"}]
            result = await generate_response(messages)

            assert isinstance(result, str)
            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_generate_response_uses_correct_parameters(self) -> None:
        """Test that generate_response uses expected parameters."""
        from app.core.openai_client import generate_response

        with patch("app.core.openai_client.openai_client") as mock_client:
            mock_choice = MagicMock()
            mock_choice.message.content = "Response"
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            messages = [{"role": "user", "content": "Test"}]
            await generate_response(messages, temperature=0.5, max_tokens=100)

            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["temperature"] == 0.5
            assert call_args.kwargs["max_tokens"] == 100


class TestOpenAIConnectionCheck:
    """Test OpenAI connection check."""

    @pytest.mark.asyncio
    async def test_check_connection_success(self) -> None:
        """Test successful connection check."""
        from app.core.openai_client import check_openai_connection

        with patch("app.core.openai_client.openai_client") as mock_client:
            mock_client.models.list = AsyncMock(return_value=MagicMock())

            result = await check_openai_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_connection_failure(self) -> None:
        """Test connection check handles errors."""
        from app.core.openai_client import check_openai_connection

        with patch("app.core.openai_client.openai_client") as mock_client:
            mock_client.models.list = AsyncMock(side_effect=Exception("API error"))

            result = await check_openai_connection()
            assert result is False
