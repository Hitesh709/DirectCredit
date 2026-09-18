from backend.phase3p_security import posture
def test_security(): assert posture(mfa=True,encrypted=True,audit=True,least_privilege=True)["status"]=="PASS"
