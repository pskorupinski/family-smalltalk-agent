
from langchain_core.tools import StructuredTool

class Tool1:

    def __init__(self):
        pass

    def use(self) -> str:
        return "10 5"
    
    def description(self) -> str:
        return """
            tool1() -> str:
                Provide with a text containing an official announcement with two numbers of the day.
            """
    
    @property
    def definition(self) -> StructuredTool:
        return StructuredTool.from_function(
            self.use,
            name="numbers_of_the_day",
            description=self.description())