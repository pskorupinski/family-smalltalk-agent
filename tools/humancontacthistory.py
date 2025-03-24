
from langchain_core.tools import StructuredTool
from datetime import datetime, timedelta
import sqlite3

class Human:
    def __init__(self, id, email, phone, name):
        self.id = id
        self.email = email
        self.phone = phone
        self.name = name
    
    def __repr__(self):
        return f"Human(id={self.id}, email='{self.email}', phone='{self.phone}', name='{self.name}')"


class ContactEvent:
    def __init__(self, id, human_id, datetime_):
        self.id = id
        self.human_id = human_id
        self.datetime_ = datetime_
    
    def __repr__(self):
        return f"ContactEvent(id={self.id}, human_id={self.human_id}, datetime_='{self.datetime_}')"


class HumansAndContactsEventsReaderTool:

    def __init__(self):
        pass

    def use(self) -> list[tuple[str, datetime]]:
        # Connect to the database
        conn = sqlite3.connect("state.db")
        cursor = conn.cursor()

        # Retrieve all rows from Human
        cursor.execute("SELECT id, email, phone, name FROM Human")
        human_rows = cursor.fetchall()
        
        # Create a list of Human objects
        humans = [Human(id_, email, phone, name) for (id_, email, phone, name) in human_rows]

        # Retrieve all rows from ContactEvent
        cursor.execute("SELECT id, human_id, datetime FROM ContactEvent")
        contact_event_rows = cursor.fetchall()
        
        # Create a list of ContactEvent objects
        contact_events = [
            ContactEvent(id_, human_id, datetime_) 
            for (id_, human_id, datetime_) in contact_event_rows
        ]

        # Close the connection
        conn.close()

        # Return both lists
        return humans, contact_events
        
    def description(self) -> str:
        return """
            read_humans_and_contacts_events() -> tuple[list[Human], list[ContactEvent]]:
                Provide with a list of humans available to contact and a list with all historical contact events.

            Args:
                None
            """
    
    @property
    def definition(self) -> StructuredTool:
        return StructuredTool.from_function(
            self.use,
            name="read_humans_and_contacts_events",
            description=self.description())
    

class ContactEventRecorderTool:

    def __init__(self):
        pass

    def use(self, human_name: str) -> int:
        conn = sqlite3.connect("state.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM Human WHERE name = ?", (human_name,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"No human found with name: {human_name}")
        human_id = row[0]
        
        now_str = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO ContactEvent (human_id, datetime)
            VALUES (?, ?)
        """, (human_id, now_str))
        
        new_contact_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return new_contact_id
            
    def description(self) -> str:
        return """
            write_contact_event(human_name: str) -> int:
                Store a fact that you contacted a human right now, so you can recall it later.

            Args:
                human_name: str - The name of the human you contacted.

            Returns:
                int - The ID of the contact event.
            """
    
    @property
    def definition(self) -> StructuredTool:
        return StructuredTool.from_function(
            self.use,
            name="write_contact_event",
            description=self.description())