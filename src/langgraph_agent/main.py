from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage

from .agent import agent


def main():
    config = {
        "configurable": {
            "thread_id": "demo-thread-1",
        }
    }

    first = agent.invoke(
        {
            "messages": [
                HumanMessage(content="My name is Sajid.")
            ]
        },
        config=config,
    )

    print("First:", first["messages"][-1].content)

    second = agent.invoke(
        {
            "messages": [
                HumanMessage(content="What is my name?")
            ]
        },
        config=config,
    )

    print("Second:", second["messages"][-1].content)


if __name__ == "__main__":
    main()