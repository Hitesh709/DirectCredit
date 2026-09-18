from backend.phase3l_api_platform import contract
def test_contract(): assert contract()["version"].endswith("3L-v1")
