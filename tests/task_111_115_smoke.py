import importlib


def test_missing_function_modules_import():
    for name in ('backend.mbl_scorecard','backend.collection_routes','backend.bank_analysis_routes','backend.settlement_routes'):
        importlib.import_module(name)


def test_official_scorecard_max_and_approval_matrix():
    from backend.mbl_scorecard import calculate, MAX_POINTS, VERSION
    result=calculate({'ownership_proof':'applicant','business_owned':True,'residence_owned':True,'business_geography':'tier1','age':40,'cibil_unsecured_enquiries_30d':0,'cibil_repayment':'none','unsecured_loans_50k_plus':3,'avg_monthly_bank_credits':500000,'bank_bounces_3m':0,'aqb':15000,'ecs_returns_12m':0,'business_type':'trader','business_vintage_years':3,'business_stock':500000,'monthly_emi_obligation':20000,'foir':0.40,'trade_validations':6,'gst_years':3,'gstr3b_avg_monthly_turnover':500000,'itr_income':500000,'mobile_stability_years':6})
    assert MAX_POINTS == 125 and VERSION == 'MBL-125-v1'; assert result.score == 125; assert result.decision == 'APPROVE' and result.approval_percent == 100


def test_official_scorecard_hard_reject_overrides_score():
    from backend.mbl_scorecard import calculate
    result=calculate({'age':40,'business_vintage_years':3,'cibil_unsecured_enquiries_30d':6})
    assert result.decision == 'REJECT'; assert 'cibil_enquiries_above_5' in result.hard_rejects


def test_scorecard_accepts_percent_foir_input():
    from backend.mbl_scorecard import calculate
    decimal=calculate({'foir':0.40,'age':40,'business_vintage_years':3,'trade_validations':1})
    percent=calculate({'foir':40,'age':40,'business_vintage_years':3,'trade_validations':1})
    assert decimal.factor_scores['foir'] == 5
    assert percent.factor_scores['foir'] == 5


def test_reporting_contains_sample_matrix_contracts():
    from backend.reporting import reporting
    assert callable(reporting); assert 'Counter' in reporting.__code__.co_names


def test_reporting_source_includes_reference_sections():
    from backend.reporting import reporting
    names=reporting.__code__.co_names
    assert 'bank_analysis' in names and 'risk_score' in names and 'loan_trend' in names and 'collection_agent_performance' in names


def test_collection_and_bank_routes_are_exposed():
    from backend.main import app
    paths=set(app.openapi().get('paths',{}))
    assert '/api/services/collection/agents' in paths
    assert '/api/services/collection/agents/performance' in paths
    assert '/api/services/bank-analysis/{customer_id}/transactions' in paths
    assert '/api/services/bank-analysis/{customer_id}/summary' in paths
    assert '/api/services/settlement/loan/{loan_id}/quote' in paths
    assert '/api/services/settlement/{settlement_id}/complete' in paths


def test_loan_model_has_persisted_score_fields():
    from backend.db_models import LoanRecord
    for name in ('scorecard_score','scorecard_max','scorecard_version','scorecard_decision','scorecard_approval_percent','scorecard_reasons','scorecard_hard_rejects','scorecard_factor_scores'): assert hasattr(LoanRecord,name)


def test_operational_models_exist():
    from backend.db_models import CollectionAgentRecord, CollectionActionRecord, BankTransactionRecord, SettlementRecord
    assert CollectionAgentRecord.__tablename__ == 'collection_agents'; assert CollectionActionRecord.__tablename__ == 'collection_actions'; assert BankTransactionRecord.__tablename__ == 'bank_transactions'; assert SettlementRecord.__tablename__ == 'loan_settlements'
