
from langchain_core.tools import StructuredTool
from datetime import datetime, timedelta
import asyncio
from sagemcom_api.client import SagemcomClient
from sagemcom_api.enums import EncryptionMethod
from sagemcom_api.exceptions import NonWritableParameterException

class HumanAvailabilityVerifierTool:

    def __init__(self):
        pass

    async def _use_async(self, human_phone_handle: str) -> bool:
        async with SagemcomClient("192.168.1.1", "1234", "*Bamb!n!Inf!n!t!*0524", EncryptionMethod.MD5, verify_ssl=True) as client:
            try:
                await client.login()
            except Exception as exception:
                print(exception)
                return None
        
            devices = await client.get_hosts()

            for device in devices:
                if(device.active and device.id == human_phone_handle):
                    return True

            return False

    def use(self, human_phone_handle: str) -> bool:
        return asyncio.run(self._use_async(human_phone_handle))
    
    def description(self) -> str:
        return """
            human_availability_verifier() -> bool:
                This tool is used to verify if a human is available to receive a message.

            Args:
                human_phone_handle: str - The phone handle of the human to verify availability.

            Returns:
                bool - True if the human is available, False otherwise.
            """
    
    @property
    def definition(self) -> StructuredTool:
        return StructuredTool.from_function(
            self.use,
            name="human_availability_verifier",
            description=self.description())
    

if __name__ == "__main__":
    tool = HumanAvailabilityVerifierTool()
    print(tool.use("B2:66:C2:5D:17:71"))