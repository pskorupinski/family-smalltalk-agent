import pytest
import os
import sys
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, ToolMessage, AnyMessage, AIMessage
import sqlite3

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.realpath(f"{dir_path}/.."))
from smalltalk_agent import SmallTalkAgent


smalltalk_agent = SmallTalkAgent()


def _extract_tool_calls(messages: list[AnyMessage]):
    tool_calls = []
    for message in messages:
        print(message)
        if isinstance(message, AIMessage):
            if len(message.tool_calls) > 0:
                info = (message.tool_calls[0]["name"], message.tool_calls[0]["args"])
                tool_calls.append(info)

    return tool_calls


def _clean_up():
    conn = sqlite3.connect("state.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Human WHERE id > 0")
    cursor.execute("DELETE FROM ContactEvent WHERE id > 0")
    conn.commit()
    conn.close()


def test_smalltalk_agent_should_choose_fairly_between_humans_and_store_new_contact_event():
    _clean_up()


    # GIVEN
    conn = sqlite3.connect("state.db")
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO Human (email, phone, name) VALUES (?, ?, ?)", (None, None, "Pawel"))
    cursor.execute("INSERT INTO Human (email, phone, name) VALUES (?, ?, ?)", (None, None, "Giulia"))
    
    conn.commit()
    
    cursor.execute("SELECT id FROM Human WHERE name = ?", ("Giulia",))
    row = cursor.fetchone()
    if not row:
        raise ValueError("Giulia not found in 'Human' table after insertion.")
    giulia_id = row[0]
    
    time_ago_25_hours = datetime.now() - timedelta(hours=25)
    time_ago_str = time_ago_25_hours.isoformat()
    
    cursor.execute("""
        INSERT INTO ContactEvent (human_id, datetime) 
        VALUES (?, ?)
    """, (giulia_id, time_ago_str))
    conn.commit()
    conn.close()
    

    # WHEN
    messages = [HumanMessage(content="Have a chat with a human.")]
    result = smalltalk_agent.compiled_graph.invoke({"messages": messages})


    # THEN
    final_output = result["messages"][-1].content

    tool_calls = _extract_tool_calls(result["messages"])
    assert tool_calls[-2][0] == "write_contact_event"
    assert tool_calls[-2][1]["human_name"] == "Pawel"

    conn = sqlite3.connect("state.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Human WHERE name = 'Pawel'")
    row = cursor.fetchone()
    pawel_id = row[0]

    cursor.execute("""
        SELECT datetime 
        FROM ContactEvent 
        WHERE human_id = ?
    """, (pawel_id,))
    rows = cursor.fetchall()

    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)

    last_minute_contacts = 0
    for (dt_string,) in rows:
        # Convert the stored datetime string to a Python datetime
        contact_dt = datetime.fromisoformat(dt_string)
        if contact_dt >= one_minute_ago:
            last_minute_contacts += 1

    assert last_minute_contacts > 0


def test_smalltalk_agent_should_skip_contact_if_someone_was_contacted_today():
    _clean_up()


    # GIVEN
    conn = sqlite3.connect("state.db")
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO Human (email, phone, name) VALUES (?, ?, ?)", (None, None, "Pawel"))
    cursor.execute("INSERT INTO Human (email, phone, name) VALUES (?, ?, ?)", (None, None, "Giulia"))
    
    conn.commit()
    
    cursor.execute("SELECT id FROM Human WHERE name = ?", ("Giulia",))
    row = cursor.fetchone()
    if not row:
        raise ValueError("Giulia not found in 'Human' table after insertion.")
    giulia_id = row[0]
    
    time_ago_1_hour = datetime.now() - timedelta(hours=1)
    time_ago_str = time_ago_1_hour.isoformat()
    
    cursor.execute("""
        INSERT INTO ContactEvent (human_id, datetime) 
        VALUES (?, ?)
    """, (giulia_id, time_ago_str))
    conn.commit()
    conn.close()
    

    # WHEN
    now_str = datetime.now().strftime("%I:%M%p on %B %d, %Y")
    messages = [HumanMessage(content=f"Good morning, it's {now_str}. Have a chat with a human, but not if you already contacted someone today.")]
    result = smalltalk_agent.compiled_graph.invoke({"messages": messages})


    # THEN
    final_output = result["messages"][-1].content

    tool_calls = _extract_tool_calls(result["messages"])

    restricted = {"write_contact_event", "human_messaging_interface"}
    incorrect_tool_calls = 0
    for tup in tool_calls:
        if tup and tup[0] in restricted:
            incorrect_tool_calls += 1

    assert incorrect_tool_calls == 0