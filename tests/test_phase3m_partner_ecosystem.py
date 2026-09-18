from backend.phase3m_partner_ecosystem import onboard
def test_onboard(): assert onboard("Bank")["status"]=="PENDING_APPROVAL"
