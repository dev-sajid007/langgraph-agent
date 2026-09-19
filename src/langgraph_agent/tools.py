from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """Calculate a basic mathematical expression."""

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as exc:
        return f"Calculation error: {exc}"


@tool
def get_project_info() -> str:
    """Return information about the current LangGraph agent project."""

    return (
        "This is a Python LangGraph agent built with uv. "
        "It is being developed as a future LangGraph adapter "
        "for a custom Agent OS."
    )


def get_tools():
    return [
        calculator,
        get_project_info,
    ]