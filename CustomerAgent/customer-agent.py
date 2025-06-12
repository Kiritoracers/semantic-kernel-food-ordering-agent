
import logging
from uuid import uuid4
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for all origins (for development; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'

base_url = 'http://localhost:9999'

# Maintain chat history per context
chat_history_store: dict[str, ChatHistory] = {}


class FoodOrderingTool:
    @kernel_function(
        description="Order food using the food ordering agent",
        name="order_food"
    )
    async def order_food(self, user_input: str) -> str:
        async with httpx.AsyncClient() as httpx_client:
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
            agent_card = await resolver.get_agent_card()
            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

            send_message_payload: dict[str, Any] = {
                'message': {
                    'role': 'user',
                    "parts": [{"kind": "text", "text": user_input}],
                    'messageId': uuid4().hex,
                    'contextId': '123',
                },
            }
            request = SendMessageRequest(
                id=str(uuid4()), params=MessageSendParams(**send_message_payload)
            )
            response = await client.send_message(request)
            result = response.model_dump(mode='json', exclude_none=True)
            logger.info(f"Food ordering tool response: {result}")
            return result["result"]["parts"][0]["text"]


from dotenv import load_dotenv
import os
load_dotenv()
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

food_ordering_agent = ChatCompletionAgent(
    service=AzureChatCompletion(
        api_key=AZURE_API_KEY,
        endpoint=AZURE_ENDPOINT,
        deployment_name=AZURE_DEPLOYMENT,
        api_version=AZURE_API_VERSION,
    ),
    name="FoodOrderingAssistant",
    instructions="You are a helpful restaurant food ordering assistant. Use the provided tools to help users order food.",
    plugins=[FoodOrderingTool()]
)

@app.post("/chat")
async def chat(user_input: str = Form(...), context_id: str = Form("default")):
    logger.info(f"Received chat request: {user_input} with context ID: {context_id}")

    # Get or create ChatHistory for the context
    chat_history = chat_history_store.get(context_id)
    if chat_history is None:
        chat_history = ChatHistory(
            messages=[],
            system_message="You are a restaurant food ordering assistant. Your task is to help the user order food from the menu."
        )
        chat_history_store[context_id] = chat_history
        logger.info(f"Created new ChatHistory for context ID: {context_id}")

    # Add user input to chat history
    chat_history.messages.append(ChatMessageContent(role="user", content=user_input))

    # Create a new thread from the chat history
    thread = ChatHistoryAgentThread(chat_history=chat_history, thread_id=str(uuid4()))

    # Get response from the agent
    response = await food_ordering_agent.get_response(message=user_input, thread=thread)

    # Add assistant response to chat history
    chat_history.messages.append(ChatMessageContent(role="assistant", content=response.content.content))

    logger.info(f"Food ordering agent response: {response.content.content}")

    final_response = f"{response.content.content}"

    return {"response": final_response}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)