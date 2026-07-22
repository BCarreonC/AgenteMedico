from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):

    message: str

    history: List[Dict[str, str]]

    intent: str

    confidence: float

    entities: Dict[str, Any]

    tool: Optional[str]

    tool_input: Dict[str, Any]

    tool_result: Any

    response: str

    errors: List[str]