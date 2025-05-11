# backend/config/memory.py
class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, session_id):
        self.sessions[session_id] = []

    def get_history(self, session_id):
        return self.sessions.get(session_id, [])

    def add_message(self, session_id, user_input, ai_response):
        self.sessions[session_id].append((user_input, ai_response))

    def get_full_history(self, session_id):
        return self.sessions.get(session_id, [])