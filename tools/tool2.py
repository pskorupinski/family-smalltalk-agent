
from langchain_core.tools import StructuredTool

class Tool2:

    def __init__(self):
        pass

    def use(self, a: int, b: int) -> str:
        return a / b
    
    def description(self) -> str:
        return """
            tool2(a: int, b: int) -> float:
                Divide a and b
            """
    
    @property
    def definition(self) -> StructuredTool:
        return StructuredTool.from_function(
            self.use,
            name="divide",
            description=self.description())