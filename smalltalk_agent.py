import base64
from typing import List, TypedDict, Annotated, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from langfuse.callback import CallbackHandler
from IPython.display import Image, display
from dotenv import load_dotenv
import os
from datetime import datetime

from tools.humancontacthistory import HumansAndContactsEventsReaderTool, ContactEventRecorderTool
from tools.humanmessaginginterface import HumanMessagingInterfaceTool
from tools.nextcontactschedule import NextContactScheduleTool
from tools.humanavailabilityverifier import HumanAvailabilityVerifierTool

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()


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
        # self._tool4 = NextContactScheduleTool()
        self._tool5 = HumanAvailabilityVerifierTool()

        self._tools = [
            self._tool1.definition,
            self._tool2.definition,
            self._tool3.definition,
            # self._tool4.definition,
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
        self._graph = builder.compile().with_config({"callbacks": [langfuse_handler]})

    def _assistant(self, state: AgentState):
        sys_msg = SystemMessage(
            content=f"""
            You are a very kind agent. Your name is Household Helper. You want to message a group of humans regularly, but you do not want that anyone feels overwhelmed by your messages.
            
            In order to achieve your goal, you want to:
            - Understand the history of your interactions with the humans. You want to be very fair and considerate when choosing which human to message, analyzing the patterns of the past interactions.
            - Verify if the human is available to receive a message. You shall never contact a human that is not available at a moment.

            When preparing a message, you want to be very kind and friendly and in that tone engage a human in a small talk, address them by name. In the first message, you want to:
            - Provide a precise and concise rationale why you chose them today over other humans. Refer to the facts from the history of your interactions with them, today's availability of others humans, and the fact that you want to be fair and considerate. Do not come up with anything. Remember, if they receive a message from you, they deserve to understand why you chose them. Otherwise, they'll lose trust in you.
            - Ask a little engaging question.

            If the human responds to your message, you may want to send a follow up message, following the same tone and style as in the first message. If there are any limitations on the length of the exchange specified in the user message, you want to follow those limitations.

            Remember to:
            - Keep a record of all your contact events, so you can take fair and considerate decisions in the future. You want to record each of your attempts to contact a human, no matter if they respond or not.

            You have these tools at your disposal:
            - {self._tool1.description()}
            - {self._tool2.description()}
            - {self._tool3.description()}
            - {self._tool5.description()}

            Current date and time is {datetime.now().strftime("%I:%M%p on %B %d, %Y")}.
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
