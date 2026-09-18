from backend.phase3j_data_platform import quality
def test_quality(): assert quality(rows=100,nulls=1)['status']=='REVIEW'