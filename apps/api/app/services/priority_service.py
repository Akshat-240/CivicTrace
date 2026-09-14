class PriorityService:
    def __init__(self, session):
        self.session = session
    async def compute_priority(self, incident_id):
        class MockPriority:
            final_priority = "high"
            severity_score = 80
            ambiguity_score = 10
            explanation = "Mock"
            safety_risk = False
            severity = "high"
            persistence_score = 0.5
        return MockPriority()
