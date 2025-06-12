import logging
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import SemanticKernelFoodOrderingAgentExecutor  # type: ignore[import-untyped]


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting Semantic Kernel Food Ordering Agent Server.")


    # Define the food ordering skill
    food_ordering_skill = AgentSkill(
        id='food_ordering',
        name='Food Ordering',
        description='Assists users in ordering food from the restaurant menu.',
        tags=['food', 'ordering', 'restaurant'],
        examples=[
            'Order a Margherita pizza and a Coke.',
            'I would like two cheeseburgers and fries.',
        ],
    )


    # Public-facing agent card for the food ordering agent
    food_ordering_agent_card = AgentCard(
        name='Semantic Kernel Food Ordering Agent',
        description='An agent that helps users order food from a restaurant using semantic kernel capabilities.',
        capabilities=AgentCapabilities(streaming=True),
        url='http://localhost:9999/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        skills=[food_ordering_skill],
        supportsAuthenticatedExtendedCard=False,
    )

    # Initialize request handler with the food ordering agent executor
    request_handler = DefaultRequestHandler(
        agent_executor=SemanticKernelFoodOrderingAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create and run the server application
    server = A2AStarletteApplication(
        agent_card=food_ordering_agent_card,
        http_handler=request_handler,
    )

    logger.info("Starting Semantic Kernel Food Ordering Agent server on port 9999.")
    uvicorn.run(server.build(), host='0.0.0.0', port=9999)