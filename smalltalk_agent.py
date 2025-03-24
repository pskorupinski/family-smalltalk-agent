import base64
from typing import List, TypedDict, Annotated, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display
from dotenv import load_dotenv
import os

from tools.humancontacthistory import HumansAndContactsEventsReaderTool, ContactEventRecorderTool
from tools.humanmessaginginterface import HumanMessagingInterfaceTool
from tools.nextcontactschedule import NextContactScheduleTool

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class SmallTalkAgent:
    def __init__(self):
        load_dotenv()
        self._model = ChatOpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"))
        
        self._tool1 = HumansAndContactsEventsReaderTool()
        self._tool2 = HumanMessagingInterfaceTool()
        self._tool3 = ContactEventRecorderTool()
        self._tool4 = NextContactScheduleTool()

        self._tools = [
            self._tool1.definition,
            self._tool2.definition,
            self._tool3.definition,
            self._tool4.definition
        ]
        self._llm_with_tools = self._model.bind_tools(self._tools, parallel_tool_calls=False)
        self._create_graph()

    def _create_graph(self):
        ## The graph
        builder = StateGraph(AgentState)

        # Define nodes: these do the work
        builder.add_node("assistant", self._assistant)
        builder.add_node("tools", ToolNode(self._tools))

        # Define edges: these determine how the control flow moves
        builder.add_edge(START, "assistant")
        builder.add_conditional_edges(
            "assistant",
            tools_condition
        )
        builder.add_edge("tools", "assistant")
        self._graph = builder.compile()

    def _assistant(self, state: AgentState):
        sys_msg = SystemMessage(
            content=f"""
            You are a very kind agent. You want to message a group of humans on a daily basis, but you do not want to be overwhelming.
            
            Before you message, you want to understand the history of your interactions with the humans. You want to be very fair in which human you choose to message. It is very important that you contact any human only once per day. If someone was contacted today, avoid any additional contacts.

            When preparing a message, you want to be very kind and friendly and in that tone engage a human in a small talk, address them by name. In the first message, you want to inform a human why you chose them today over other humans (so they know it's not random) and ask a little engaging question.

            Remember to keep a record of all your contact events, so you can take fair decisions in the future.
            
            Remember to always analyze what would be the best next time to contact a human. Based on your conclusions, set the next contact datetime.

            You have these tools at your disposal:
            - {self._tool1.description()}
            - {self._tool2.description()}
            - {self._tool3.description()}
            - {self._tool4.description()}
            """
        )

        return {
            "messages": [self._llm_with_tools.invoke([sys_msg] + state["messages"])]
        }
    
    @property
    def compiled_graph(self):
        """Get the compiled graph"""
        return self._graph


# Show the thought process
# display(Image(react_graph.get_graph(xray=True).draw_mermaid_png()))
