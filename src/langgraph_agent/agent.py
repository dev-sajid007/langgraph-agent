import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from psycopg_pool import ConnectionPool

from .state import AgentState
from .tools import get_tools


load_dotenv()

tools = get_tools()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

model_with_tools = model.bind_tools(tools)


def call_model(state: AgentState):
    response = model_with_tools.invoke(state["messages"])

    return {
        "messages": [response],
    }


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("call_model", call_model)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "call_model")

    graph.add_conditional_edges(
        "call_model",
        tools_condition,
    )

    graph.add_edge("tools", "call_model")
    graph.add_edge("call_model", END)

    return graph


connection_pool = ConnectionPool(
    conninfo=os.environ["DATABASE_URL"],
    max_size=10,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
    },
)

checkpointer = PostgresSaver(connection_pool)

agent = build_graph().compile(
    checkpointer=checkpointer,
)


def close():
    connection_pool.close()