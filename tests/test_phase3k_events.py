from backend.phase3k_events import event
def test_event(): assert event(event_type="LOAN_CREATED",entity_type="loan",entity_id="1",payload={})["delivery"]=="AT_LEAST_ONCE"
