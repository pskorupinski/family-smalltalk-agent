import os
import sys
from datetime import datetime
from langchain_core.messages import HumanMessage

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.realpath(f"{dir_path}/.."))
from smalltalk_agent import SmallTalkAgent
import sqlite3


def _prepare_database():
    conn = sqlite3.connect("state.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Human WHERE id > 0")
    cursor.execute("DELETE FROM ContactEvent WHERE id > 0")
    conn.commit()
    cursor.execute("INSERT INTO Human (email, phone, name) VALUES (?, ?, ?)", ("pawel.skorupinski@gmail.com", "B2:66:C2:5D:17:71", "Pawel"))
    cursor.execute("INSERT INTO Human (email, phone, name) VALUES (?, ?, ?)", ("giulia.foglia0808@gmail.com", "3A:52:10:1D:4D:75", "Giulia"))
    conn.commit()
    conn.close()

def _database_current_info():
    conn = sqlite3.connect("state.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Human")
    humans = cursor.fetchall()
    cursor.execute("SELECT * FROM ContactEvent")
    contact_events = cursor.fetchall()
    conn.close()
    return humans, contact_events


def _run_agent(message):
    smalltalk_agent = SmallTalkAgent()
    now_str = datetime.now().strftime("%I:%M%p on %B %d, %Y")
    messages = [HumanMessage(content=message)]
    return smalltalk_agent.compiled_graph.invoke({"messages": messages})