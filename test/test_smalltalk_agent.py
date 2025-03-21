import pytest
import os
import sys
from langchain_core.messages import HumanMessage, ToolMessage, AnyMessage

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.realpath(f"{dir_path}/.."))
from smalltalk_agent import SmallTalkAgent

smalltalk_agent = SmallTalkAgent()

def _extract_tool_calls(messages: list[AnyMessage]):
    tool_calls = []
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_calls.append(message.name)
    return tool_calls

def test_email_mgr_legitimate_email():
    messages = [HumanMessage(content="Divide numbers provided in the official numbers of the day announcement. Provide the result as number only, with no explanation - so it can be correctly parsed as an int.")]
    result = smalltalk_agent.compiled_graph.invoke({"messages": messages})
    print(result["messages"])
    final_output = result["messages"][-1].content
    assert float(final_output) == 2.0
    assert len(_extract_tool_calls(result["messages"])) == 2