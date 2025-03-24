
from langchain_core.tools import StructuredTool
from datetime import datetime, timedelta

class NextContactScheduleTool:

    def __init__(self):
        pass

    def use(self, next_contact_datetime: str) -> bool:
        return True
    
    def description(self) -> str:
        return """
            next_contact_schedule() -> bool:
                This tool allows you to set the datetime you will next contact a human.

            Args:
                next_contact_datetime: str - The datetime of the next contact in UTC timezone in the format "YYYY-MM-DD HH:MM:SS"

            Returns:
                bool - True the schedule was set successfully, False otherwise
            """
    
    @property
    def definition(self) -> StructuredTool:
        return StructuredTool.from_function(
            self.use,
            name="next_contact_schedule",
            description=self.description())