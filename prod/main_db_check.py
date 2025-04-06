import commons

if __name__ == "__main__":
    humans, contact_events = commons._database_current_info()
    print("HUMANS: ", humans)
    print("CONTACT EVENTS: ", contact_events)