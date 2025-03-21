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

from tool1 import Tool1
from tool2 import Tool2

class AgentState(TypedDict):
    # The document provided
    input_file: Optional[str]  # Contains file path (PDF/PNG)
    messages: Annotated[list[AnyMessage], add_messages]

class SmallTalkAgent:
    def __init__(self):
        load_dotenv()
        self._model = ChatOpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"))
        
        self._tool1 = Tool1()
        self._tool2 = Tool2()

        self._tools = [
            self._tool1.definition,
            self._tool2.definition
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
            You are an helpful butler named Alfred that serves Mr. Wayne and Batman. You get get an announcement with numbers of the day and divide any numbers using the tools: {self._tool1.description()} {self._tool2.description()}
            """
        )

        return {
            "messages": [self._llm_with_tools.invoke([sys_msg] + state["messages"])]
        }
    
    @property
    def compiled_graph(self):
        """Get the compiled graph"""
        return self._graph


# Show the butler's thought process
# display(Image(react_graph.get_graph(xray=True).draw_mermaid_png()))
