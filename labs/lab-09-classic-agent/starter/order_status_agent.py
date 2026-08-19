"""Builds a classic agent with function tools for order lookups, and
exercises it across a multi-turn thread.
"""

from __future__ import annotations

from mock_orders_api.orders import OrderNotFoundError, get_order_status, list_orders_for_customer

ORDER_STATUS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "Look up the status, items, and shipping info for one Cascadia order.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID, e.g. CO-10231"}},
            "required": ["order_id"],
        },
    },
}

LIST_ORDERS_TOOL = {
    "type": "function",
    "function": {
        "name": "list_orders_for_customer",
        "description": "List every order for a customer, most recent first.",
        "parameters": {
            "type": "object",
            "properties": {"customer_email": {"type": "string"}},
            "required": ["customer_email"],
        },
    },
}


def create_order_status_agent(agents_client, *, model: str):
    """Creates the classic agent with both order-lookup tools attached."""
    # TODO(lab-09): call agents_client.create_agent() with model, a name,
    # instructions, and tools=[ORDER_STATUS_TOOL, LIST_ORDERS_TOOL].
    raise NotImplementedError("create_order_status_agent is not implemented yet")


def execute_tool(tool_name: str, args: dict):
    """Dispatches one tool call to its real implementation."""
    # TODO(lab-09): if tool_name == "get_order_status", call
    # get_order_status(args["order_id"]); catch OrderNotFoundError and
    # return {"error": ...} instead of raising.
    #
    # TODO(lab-09): if tool_name == "list_orders_for_customer", call
    # list_orders_for_customer(args["customer_email"]).
    #
    # TODO(lab-09): otherwise, raise ValueError(f"Unknown tool: {tool_name}").
    raise NotImplementedError("execute_tool is not implemented yet")


def ask_in_thread(agents_client, thread_id: str, agent_id: str, question: str) -> str:
    """Adds one message to an existing thread and returns the agent's reply."""
    # TODO(lab-09): add a user message to thread_id, process a run with
    # tool_executor=execute_tool, then return the last message's content.
    raise NotImplementedError("ask_in_thread is not implemented yet")


def main() -> None:
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    agent = create_order_status_agent(client.agents, model=os.environ.get("LOW_COST_DEPLOYMENT", "cascadia-low-cost"))
    thread = client.agents.create_thread()

    reply_1 = ask_in_thread(client.agents, thread.id, agent.id, "What's the status of order CO-10231?")
    print(f"Turn 1: {reply_1}")

    reply_2 = ask_in_thread(client.agents, thread.id, agent.id, "What about CO-10245?")
    print(f"Turn 2: {reply_2}")


if __name__ == "__main__":
    main()
