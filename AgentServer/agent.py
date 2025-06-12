import asyncio
import logging
from uuid import uuid4

from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticKernelFoodOrderingAgent:


    async def order_food(self, user_input: str, context_id: str) -> str:
        """
        Order food based on user input.
        :param user_input: The user's food order.
        :param context_id: The context ID for the request.
        :return: The response from the food ordering agent.
        """
        logger.info(f"Received food order request: {user_input} with context ID: {context_id}")
        if not user_input:
            logger.error("User input is empty.")
            raise ValueError("User input cannot be empty.")
        # Get or create ChatHistory for the context
        chat_history = self.history_store.get(context_id)
        if chat_history is None:
            chat_history = ChatHistory(
                messages=[],
                system_message="You are a helpful restaurant food ordering assistant. Your task is to help the user order food from the menu. If all information is correct, mock the response of successful food ordering."
            )
            self.history_store[context_id] = chat_history
            logger.info(f"Created new ChatHistory for context ID: {context_id}")
        chat_history.messages.append(ChatMessageContent(role="user", content=user_input))
        thread = ChatHistoryAgentThread(chat_history=chat_history, thread_id=str(uuid4()))
        response = await self.chat_agent.get_response(message=user_input, thread=thread)
        chat_history.messages.append(ChatMessageContent(role="assistant", content=response.content.content))
        logger.info(f"Food ordering agent response: {response.content.content}")
        final_response = f"{response.content.content}\n\nThis is a food ordering agent. Please provide the necessary details for your food order."
        return final_response

    def __init__(self):
        import os
        logger.info("Initializing SemanticKernelFoodOrderingAgent.")
        self.chat_agent = ChatCompletionAgent(
            service=AzureChatCompletion(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            ),
            name="Assistant",
        )
        # Mapping of context_id -> ChatHistory
        self.history_store: dict[str, ChatHistory] = {}
        logger.info("SemanticKernelFoodOrderingAgent initialized successfully.")

    # Flight booking logic removed
