from backend.phase3q_disaster_recovery import recovery_status
def test_dr(): assert recovery_status(backup_verified=True,restore_tested=True,replication=True)["status"]=="READY"
