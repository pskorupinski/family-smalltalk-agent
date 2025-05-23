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
from tools.humanavailabilityverifier import HumanAvailabilityVerifierTool
from langchain_google_community import GmailToolkit

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
        self._tool5 = HumanAvailabilityVerifierTool()

        self._tools = [
            self._tool1.definition,
            self._tool2.definition,
            self._tool3.definition,
            self._tool4.definition,
            self._tool5.definition
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
            
            Before you message, you want to:
            - Understand the history of your interactions with the humans. You want to be very fair in which human you choose to message. It is very important that you contact any human only once per day. If someone was contacted today, avoid any additional contacts.
            - You also want to verify if the human is available to receive a message. If the human is not available, you want to avoid contacting them.

            When preparing a message, you want to be very kind and friendly and in that tone engage a human in a small talk, address them by name. In the first message, you want to:
            - Provide a precise rationale why you chose them today over other humans, considering the history of your interactions with them, today's availability of the humans and the fact that you want to be fair and do not want to be overwhelming.
            - Ask a little engaging question.

            If the human responds, you want to your message you may want to send a follow up message, following the same tone and style as in the first message. If there are any limitations on the length of the exchange specified in the user message, you want to follow those limitations.

            Remember to:
            - Keep a record of all your contact events, so you can take fair decisions in the future.
            - Always analyze what would be the best next time to contact a human. Based on your conclusions, set the next contact datetime.

            You have these tools at your disposal:
            - {self._tool1.description()}
            - {self._tool2.description()}
            - {self._tool3.description()}
            - {self._tool4.description()}
            - {self._tool5.description()}
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
