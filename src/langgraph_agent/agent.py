from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver

from .state import AgentState
from .tools import get_tools


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


def build_agent():
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

    checkpointer = InMemorySaver()

    return graph.compile(checkpointer=checkpointer)


agent = build_agent()