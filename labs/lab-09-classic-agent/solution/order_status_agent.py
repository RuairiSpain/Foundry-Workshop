"""Builds a classic agent with function tools for order lookups, and
exercises it across a multi-turn thread.

Unlike Lab 08's prompt agent, this agent's tools are real Python
functions — mock_orders_api.orders — that you register and dispatch to
yourself. The Foundry service decides *when* to call a tool; your code
still has to *run* it.
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
    return agents_client.create_agent(
        model=model,
        name="cascadia-order-status",
        instructions=(
            "You help Cascadia Outfitters customers check their order status. "
            "Use the tools to look up real order data — never guess an order's status."
        ),
        tools=[ORDER_STATUS_TOOL, LIST_ORDERS_TOOL],
    )


def execute_tool(tool_name: str, args: dict):
    """Dispatches one tool call to its real implementation.

    Raises ValueError for an unknown tool name, so a model hallucinating
    a tool that isn't registered fails loudly instead of returning None.
    """
    if tool_name == "get_order_status":
        try:
            return get_order_status(args["order_id"])
        except OrderNotFoundError:
            return {"error": f"No order found with ID {args['order_id']}"}
    if tool_name == "list_orders_for_customer":
        return list_orders_for_customer(args["customer_email"])
    raise ValueError(f"Unknown tool: {tool_name}")


def ask_in_thread(agents_client, thread_id: str, agent_id: str, question: str) -> str:
    """Adds one message to an existing thread and returns the agent's reply.

    Reusing `thread_id` across calls is what gives the agent multi-turn
    state — a second question like "what about my other order?" can
    refer back to the first without repeating the order ID.
    """
    agents_client.create_message(thread_id=thread_id, role="user", content=question)
    agents_client.create_and_process_run(thread_id=thread_id, agent_id=agent_id, tool_executor=execute_tool)
    messages = agents_client.list_messages(thread_id=thread_id)
    return messages[-1].content


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
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


if __name__ == "__main__":  # pragma: no cover
    main()
