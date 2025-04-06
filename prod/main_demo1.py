import commons

if __name__ == "__main__":
    message = """
    Initiate a chat with a human, but not if no one is available.
    If the human sends you a response within two minutes, send a goodbye follow up message.
    """
    print("ADMIN PROMPT: ", message)
    result = commons._run_agent(message)
    print("AGENT'S ADMIN LOG: ", result["messages"][-1].content)