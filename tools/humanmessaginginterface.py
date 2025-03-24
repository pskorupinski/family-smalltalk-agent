
from langchain_core.tools import StructuredTool
from datetime import datetime, timedelta

class HumanMessagingInterfaceTool:

    def __init__(self):
        pass

    def use(self, human_name: str, message: str) -> bool:
        return True
    
    def description(self) -> str:
        return """
            human_messaging_interface() -> bool:
                This is the only inferface you have to interact with humans. You can send them a message and receive a boolean value indicating whether the message was sent successfully.

            Args:
                human_name: str - The name of the human to send the message to.
                message: str - The message to send to the human.
            """
    
    @property
    def definition(self) -> StructuredTool:
        return StructuredTool.from_function(
            self.use,
            name="human_messaging_interface",
            description=self.description())