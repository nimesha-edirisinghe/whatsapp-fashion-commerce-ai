"""AI service for generating responses using GPT."""

from typing import Any

from app.core.exceptions import OpenAIError
from app.core.logging import logger
from app.core.openai_client import openai_client
from app.services.escalation_service import escalation_service
from app.services.rag_service import rag_service
from app.services.session_service import session_service
from app.utils.retry import async_retry


class AIService:
    """Service for AI-powered response generation."""

    SYSTEM_PROMPT = """You are a helpful AI assistant for a fashion import business.
You help customers find clothing items, answer questions about products, sizes, shipping, and returns.

Guidelines:
- Be friendly and professional
- Focus only on fashion/clothing related questions
- Provide accurate information based on the context provided
- If you don't have specific information, say so honestly
- Keep responses concise and helpful
- Respond in the same language as the customer's message

Available size formats: XS, S, M, L, XL, XXL and numeric sizes (2-16 US, 34-48 EU)"""

    NON_CLOTHING_KEYWORDS = [
        "weather", "news", "politics", "sports score", "recipe",
        "math", "calculate", "code", "programming", "translate",
    ]

    @async_retry(attempts=1, timeout=3.0)
    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        conversation_history: list[dict[str, str]] | None = None,
        language: str = "en",
    ) -> str:
        """
        Generate AI response using GPT.

        Args:
            user_message: User's question
            context: Retrieved knowledge base context
            conversation_history: Previous conversation messages
            language: Detected language code

        Returns:
            Generated response text
        """
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

            # Add context if available
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Relevant information:\n{context}",
                })

            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)

            # Add current message
            messages.append({"role": "user", "content": user_message})

            response = await openai_client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o as proxy for GPT-5
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )

            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            raise OpenAIError(f"Failed to generate response: {e}") from e

    def is_clothing_related(self, message: str) -> bool:
        """
        Check if message is related to clothing/fashion.

        Args:
            message: User message

        Returns:
            True if clothing-related, False otherwise
        """
        message_lower = message.lower()

        # Check for obvious non-clothing keywords
        for keyword in self.NON_CLOTHING_KEYWORDS:
            if keyword in message_lower:
                return False

        # Clothing-related keywords
        clothing_keywords = [
            "dress", "shirt", "pants", "skirt", "jacket", "coat",
            "shoe", "size", "color", "fabric", "cotton", "silk",
            "order", "shipping", "delivery", "return", "exchange",
            "price", "cost", "available", "stock", "inventory",
            "style", "fashion", "wear", "outfit", "clothing",
            "blouse", "sweater", "jeans", "shorts", "top",
        ]

        for keyword in clothing_keywords:
            if keyword in message_lower:
                return True

        # Default to True for ambiguous messages
        # (let the AI handle it with context)
        return True

    def get_redirect_message(self, language: str = "en") -> str:
        """
        Get polite redirect message for non-clothing queries.

        Args:
            language: Language code

        Returns:
            Redirect message
        """
        messages = {
            "en": (
                "I'm here to help with fashion and clothing questions! "
                "Feel free to ask about our products, sizes, shipping, or returns. "
                "You can also send a photo of clothing you'd like to find."
            ),
            "es": (
                "¡Estoy aquí para ayudar con preguntas sobre moda y ropa! "
                "Puede preguntar sobre productos, tallas, envíos o devoluciones. "
                "También puede enviar una foto de la ropa que busca."
            ),
            "fr": (
                "Je suis là pour répondre à vos questions sur la mode ! "
                "N'hésitez pas à me poser des questions sur nos produits, tailles, livraison ou retours. "
                "Vous pouvez aussi m'envoyer une photo du vêtement que vous recherchez."
            ),
        }
        return messages.get(language, messages["en"])

    async def process_text_message(
        self,
        customer_phone: str,
        message: str,
        language: str = "en",
    ) -> str:
        """
        Process a text message and generate response.

        Full pipeline: context retrieval, history, AI generation, escalation check.

        Args:
            customer_phone: Customer phone number
            message: User message
            language: Detected language

        Returns:
            Generated response
        """
        # Check for explicit escalation request
        if escalation_service.detect_escalation_request(message):
            await self._handle_escalation(
                customer_phone=customer_phone,
                message=message,
                reason="Customer requested human assistance",
                history=await session_service.get_context(customer_phone),
            )
            return escalation_service.get_escalation_message()

        # Check if clothing-related
        if not self.is_clothing_related(message):
            return self.get_redirect_message(language)

        # Get conversation history
        history = await session_service.get_context(customer_phone)

        # Get relevant context from knowledge base
        context = await rag_service.get_relevant_context(message)

        # Generate response with confidence tracking
        response, confidence = await self.generate_response_with_confidence(
            user_message=message,
            context=context,
            conversation_history=history,
            language=language,
        )

        # Check if should escalate due to low confidence
        should_escalate, reason = escalation_service.should_escalate(confidence)
        if should_escalate:
            await self._handle_escalation(
                customer_phone=customer_phone,
                message=message,
                reason=reason,
                confidence=confidence,
                history=history,
            )
            # Still return the response, but notify about escalation
            return (
                f"{response}\n\n"
                "---\n"
                "I've also notified a team member to review this conversation "
                "in case you need additional assistance."
            )

        # Save messages to session
        await session_service.add_message(customer_phone, "user", message)
        await session_service.add_message(customer_phone, "assistant", response)

        return response

    async def generate_response_with_confidence(
        self,
        user_message: str,
        context: str = "",
        conversation_history: list[dict[str, str]] | None = None,
        language: str = "en",
    ) -> tuple[str, float]:
        """
        Generate response with confidence score.

        Returns:
            Tuple of (response_text, confidence_score)
        """
        try:
            response = await self.generate_response(
                user_message=user_message,
                context=context,
                conversation_history=conversation_history,
                language=language,
            )

            # Calculate confidence based on context availability
            # Higher confidence if we have relevant context
            confidence = 0.85 if context else 0.65

            # Lower confidence for certain phrases
            uncertain_phrases = [
                "i'm not sure",
                "i don't know",
                "i cannot",
                "unfortunately",
                "i apologize",
            ]
            if any(phrase in response.lower() for phrase in uncertain_phrases):
                confidence -= 0.2

            return response, max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.error(f"Response generation with confidence failed: {e}")
            raise

    async def _handle_escalation(
        self,
        customer_phone: str,
        message: str,
        reason: str,
        confidence: float | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> None:
        """Handle escalation to human agent."""
        await escalation_service.escalate_to_human(
            customer_phone=customer_phone,
            reason=reason,
            confidence_score=confidence,
            last_message=message,
            conversation_history=history,
        )


# Singleton instance
ai_service = AIService()
