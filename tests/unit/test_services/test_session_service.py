"""Unit tests for session service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.session_service import SessionService


class TestSessionService:
    """Tests for session service methods."""

    @pytest.fixture
    def session_service(self) -> SessionService:
        """Create session service instance."""
        return SessionService()

    @pytest.mark.asyncio
    async def test_get_context_returns_history(self, session_service: SessionService):
        """Test retrieving conversation history."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.lrange = AsyncMock(return_value=[
                '{"role": "user", "content": "Hello"}',
                '{"role": "assistant", "content": "Hi there!"}',
            ])

            context = await session_service.get_context("15559876543")

            assert len(context) == 2
            assert context[0]["role"] == "user"
            assert context[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_context_empty_history(self, session_service: SessionService):
        """Test retrieving empty conversation history."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.lrange = AsyncMock(return_value=[])

            context = await session_service.get_context("15559876543")

            assert context == []

    @pytest.mark.asyncio
    async def test_get_context_limits_messages(self, session_service: SessionService):
        """Test that history is limited to 10 messages."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            # Return 10 messages (limit)
            mock_redis.lrange = AsyncMock(return_value=[
                f'{{"role": "user", "content": "Message {i}"}}'
                for i in range(10)
            ])

            context = await session_service.get_context("15559876543")

            assert len(context) == 10
            # Verify lrange was called with proper range (last 10)
            mock_redis.lrange.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_message_user(self, session_service: SessionService):
        """Test adding user message to history."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.rpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            mock_redis.expire = AsyncMock()

            await session_service.add_message(
                "15559876543",
                "user",
                "What sizes do you have?"
            )

            mock_redis.rpush.assert_called_once()
            # Verify TTL is set (24h = 86400 seconds)
            mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_add_message_assistant(self, session_service: SessionService):
        """Test adding assistant message to history."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.rpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            mock_redis.expire = AsyncMock()

            await session_service.add_message(
                "15559876543",
                "assistant",
                "We have sizes S, M, L, XL."
            )

            mock_redis.rpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_message_trims_history(self, session_service: SessionService):
        """Test that history is trimmed to last 10 messages."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.rpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            mock_redis.expire = AsyncMock()

            await session_service.add_message(
                "15559876543",
                "user",
                "Test message"
            )

            # Verify ltrim keeps last 10 messages
            mock_redis.ltrim.assert_called_once()
            # Should keep last 10 items (-10, -1)
            # call_args is a tuple (args, kwargs) or a Call object with .args attribute
            call_args = mock_redis.ltrim.call_args
            args = call_args.args if hasattr(call_args, 'args') else call_args[0]
            assert len(args) >= 3, "ltrim should be called with key, start, and end arguments"
            assert args[1] == -10
            assert args[2] == -1

    @pytest.mark.asyncio
    async def test_add_message_sets_ttl(self, session_service: SessionService):
        """Test that 24h TTL is set on session."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.rpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            mock_redis.expire = AsyncMock()

            await session_service.add_message(
                "15559876543",
                "user",
                "Test message"
            )

            # Verify TTL is 24 hours (86400 seconds)
            mock_redis.expire.assert_called_once()
            call_args = mock_redis.expire.call_args
            args = call_args.args if hasattr(call_args, 'args') else call_args[0]
            assert args[1] == 86400

    @pytest.mark.asyncio
    async def test_clear_context(self, session_service: SessionService):
        """Test clearing conversation history."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock()

            await session_service.clear_context("15559876543")

            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_key_format(self, session_service: SessionService):
        """Test that session keys are properly formatted."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.lrange = AsyncMock(return_value=[])

            await session_service.get_context("15559876543")

            # Verify key format includes prefix and phone
            call_args = mock_redis.lrange.call_args
            args = call_args.args if hasattr(call_args, 'args') else call_args[0]
            key = args[0]
            assert "15559876543" in key
            assert "session" in key.lower() or "context" in key.lower()


class TestSessionServiceErrorHandling:
    """Error handling tests for session service."""

    @pytest.fixture
    def session_service(self) -> SessionService:
        """Create session service instance."""
        return SessionService()

    @pytest.mark.asyncio
    async def test_get_context_redis_error(self, session_service: SessionService):
        """Test graceful handling of Redis errors on get."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.lrange = AsyncMock(side_effect=Exception("Redis unavailable"))

            # Should return empty list on error (graceful degradation)
            context = await session_service.get_context("15559876543")
            assert context == []

    @pytest.mark.asyncio
    async def test_add_message_redis_error(self, session_service: SessionService):
        """Test graceful handling of Redis errors on add."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.rpush = AsyncMock(side_effect=Exception("Redis unavailable"))

            # Should not raise, just log error
            await session_service.add_message(
                "15559876543",
                "user",
                "Test message"
            )

    @pytest.mark.asyncio
    async def test_invalid_json_in_history(self, session_service: SessionService):
        """Test handling of corrupted JSON in history."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.lrange = AsyncMock(return_value=[
                '{"role": "user", "content": "Valid"}',
                'invalid json here',
                '{"role": "assistant", "content": "Also valid"}',
            ])

            context = await session_service.get_context("15559876543")

            # Should skip invalid entries and return valid ones
            assert isinstance(context, list)
            assert len(context) == 2  # Should have 2 valid entries
            assert context[0]["content"] == "Valid"
            assert context[1]["content"] == "Also valid"


class TestSessionServiceContextWindow:
    """Tests for context window management."""

    @pytest.fixture
    def session_service(self) -> SessionService:
        """Create session service instance."""
        return SessionService()

    @pytest.mark.asyncio
    async def test_context_preserves_order(self, session_service: SessionService):
        """Test that message order is preserved."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            messages = [
                '{"role": "user", "content": "First"}',
                '{"role": "assistant", "content": "Second"}',
                '{"role": "user", "content": "Third"}',
            ]
            mock_redis.lrange = AsyncMock(return_value=messages)

            context = await session_service.get_context("15559876543")

            assert context[0]["content"] == "First"
            assert context[1]["content"] == "Second"
            assert context[2]["content"] == "Third"

    @pytest.mark.asyncio
    async def test_format_for_llm(self, session_service: SessionService):
        """Test formatting context for LLM consumption."""
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.lrange = AsyncMock(return_value=[
                '{"role": "user", "content": "Hello"}',
                '{"role": "assistant", "content": "Hi!"}',
            ])

            context = await session_service.get_context("15559876543")

            # Each message should have role and content
            for msg in context:
                assert "role" in msg
                assert "content" in msg
                assert msg["role"] in ["user", "assistant"]
