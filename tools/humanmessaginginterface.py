from langchain_core.tools import StructuredTool
from datetime import datetime, timedelta
from enum import Enum
import base64
import os
import time
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class HumanMessagingInterfaceReturnStatus(Enum):
    RETURNED_WITH_RESPONSE = 0
    RETURNED_WITHOUT_AWAITING_RESPONSE = 1
    RETURNED_ON_TIMEOUT_REACHED = 2


class HumanMessagingInterfaceTool:

    def __init__(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.modify'])
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", ['https://www.googleapis.com/auth/gmail.modify']
                )
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
        
        self._service = build('gmail', 'v1', credentials=creds)

    def _send_message(self, human_email: str, message_subject: str, message_body, thread_id: str = None) -> str:
        message = MIMEText(message_body, 'plain')
        message['to'] = human_email
        if thread_id:
            message['In-Reply-To'] = thread_id
            message['References'] = thread_id
            message['subject'] = "Re: " + message_subject
        else:
            message['subject'] = message_subject
        print(message)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        if thread_id:
            sent_message = self._service.users().messages().send(
                userId='me',
                body={'raw': raw_message, 'threadId': thread_id}
            ).execute()
        else:
            sent_message = self._service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
        print(sent_message)
        thread_id = sent_message['threadId']
        return thread_id

    def _await_response(self, thread_id, response_timeout: int = 10) -> tuple[HumanMessagingInterfaceReturnStatus, str, str]:
        start_time = datetime.now()
        timeout_delta = timedelta(minutes=response_timeout)
        
        while datetime.now() - start_time < timeout_delta:
            # Get messages in thread
            thread_messages = self._service.users().threads().get(
                userId='me', 
                id=thread_id
            ).execute()
            
            # Look for unread messages in the thread
            for message in thread_messages['messages']:
                # Skip the first message (our sent message)
                if message == thread_messages['messages'][0]:
                    continue
                    
                # Check if message is unread
                if 'UNREAD' in message['labelIds']:
                    # Get message payload
                    message_data = self._service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Extract message body
                    if 'data' in message_data['payload']['body']:
                        raw_body = base64.urlsafe_b64decode(
                            message_data['payload']['body']['data']
                        ).decode('utf-8')
                    else:
                        # Handle multipart messages
                        raw_body = base64.urlsafe_b64decode(
                            message_data['payload']['parts'][0]['body']['data']
                        ).decode('utf-8')

                    # Extract only the new message content by splitting on common email markers
                    markers = [
                        "\r\n\r\nOn ",  # Common reply marker
                        "\n\nOn ",      # Alternative reply marker
                        "\r\n> ",       # Quoted text marker
                        "\n> ",         # Alternative quote marker
                        "\r\n\r\n-----Original Message-----", # Forwarded message marker
                        "\n\n-----Original Message-----"      # Alternative forward marker
                    ]
                    
                    message_body = raw_body
                    for marker in markers:
                        if marker in message_body:
                            message_body = message_body.split(marker)[0].strip()
                    
                    # Mark message as read
                    self._service.users().messages().modify(
                        userId='me',
                        id=message['id'],
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                    
                    return (HumanMessagingInterfaceReturnStatus.RETURNED_WITH_RESPONSE, message_body, thread_id)
            
            # Sleep for 1 second before trying again
            time.sleep(1)
        
        # If timeout reached without response
        return (HumanMessagingInterfaceReturnStatus.RETURNED_ON_TIMEOUT_REACHED, None, None)

    def use(self, human_email: str, message_subject: str, message_body: str, await_response: bool = False, response_timeout: int = 10, messaging_thread_handle: str = None) -> tuple[HumanMessagingInterfaceReturnStatus, str, str]:
        thread_id = self._send_message(human_email, message_subject, message_body, messaging_thread_handle)
        if await_response == True:
            return self._await_response(thread_id, response_timeout)
        else:
            return (HumanMessagingInterfaceReturnStatus.RETURNED_WITHOUT_AWAITING_RESPONSE, None, None)
    
    def description(self) -> str:
        return """
            human_messaging_interface() -> bool:
                This is the only inferface you have to interact with humans. You can send them a message and await a response. If the response is received within the response_timeout, you will receive the response and the handle to the messaging thread, in case you want to send a follow up message.

            Args:
                human_email: str - The email address of the human to send the message to.
                message_subject: str - The subject of the message to send to the human.
                message_body: str - The body of the message to send to the human.
                await_response: bool - Whether to await a response from the human.
                response_timeout: int - The timeout for the response from the human - in minutes.
                messaging_thread_handle: str - The handle to the messaging thread to use for the response in case you want to send a follow up message.

            Returns:
                tuple[HumanMessagingInterfaceReturnStatus, str, str] - A tuple containing the return status (always returned), the response from the human and the messaging thread handle (both returned only if await_response is True and the response was received within the response_timeout) and the thread id.
            """
    
    @property
    def definition(self) -> StructuredTool:
        return StructuredTool.from_function(
            self.use,
            name="human_messaging_interface",
            description=self.description())
    

if __name__ == "__main__":
    hmi = HumanMessagingInterfaceTool()
    status, response, thread_id = hmi.use("pawel.skorupinski@gmail.com", "Ciao!", "How have you been? Best, PS Agent", await_response=True, response_timeout=10)
    print(status, response, thread_id)
    status, response, thread_id = hmi.use("pawel.skorupinski@gmail.com", "Ciao!", "Awesome.", messaging_thread_handle=thread_id)
    print(status, response, thread_id)