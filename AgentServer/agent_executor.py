from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from agent import SemanticKernelFoodOrderingAgent
import logging
from a2a.utils import (
    new_agent_text_message,
    new_task,
)

logger = logging.getLogger(__name__)

class SemanticKernelFoodOrderingAgentExecutor(AgentExecutor):
    """Executor for SemanticKernelFoodOrderingAgent."""

    def __init__(self):
        logger.info("Initializing SemanticKernelFoodOrderingAgentExecutor.")
        self.agent = SemanticKernelFoodOrderingAgent()
        logger.info("SemanticKernelFoodOrderingAgentExecutor initialized successfully.")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_input = context.get_user_input()
        task = context.current_task
        context_id = context.context_id

        if not task:
            task = new_task(context.message)
            event_queue.enqueue_event(task)

        # Only food ordering supported
        logger.info(f"Executing agent with user input: {user_input} with task: {task.id} and context ID: {context_id}")
        try:
            result = await self.agent.order_food(user_input, context_id)
            logger.info("Food ordering executed successfully.")
            event_queue.enqueue_event(new_agent_text_message(result))
        except Exception as e:
            logger.error(f"Error during agent execution: {e}")
            event_queue.enqueue_event(new_agent_text_message(f"Error: {str(e)}"))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        logger.warning("Cancel operation requested but not supported.")
        raise Exception('Cancel operation not supported.')