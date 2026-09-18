from backend.phase3u_model_governance import register
def test_register(): assert register("risk","1","credit")["deployment_status"]=="NOT_APPROVED"
