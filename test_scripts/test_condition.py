from src.core.condition import ConditionFilter, NormalizedCondition


def test_exclude_broken_english():
    cf = ConditionFilter()
    assert cf.should_exclude("Broken clutch lever for parts", "") is True

def test_exclude_rotto_italian():
    cf = ConditionFilter()
    assert cf.should_exclude("Leva frizione", "Rotto, venduto per ricambi") is True

def test_exclude_kaputt_german():
    cf = ConditionFilter()
    assert cf.should_exclude("Kupplungshebel kaputt", "") is True

def test_exclude_for_parts_romanian():
    cf = ConditionFilter()
    assert cf.should_exclude("Maneta", "pentru piese de schimb") is True

def test_exclude_rusty_bulgarian():
    cf = ConditionFilter()
    assert cf.should_exclude("Лост съединител ръждясал", "") is True

def test_allow_good_condition():
    cf = ConditionFilter()
    assert cf.should_exclude("Clutch lever Multistrada 1260", "Good condition, barely used") is False

def test_allow_normal_description():
    cf = ConditionFilter()
    assert cf.should_exclude("Leva frizione Ducati", "Ottimo stato, come nuova") is False

def test_normalize_like_new():
    cf = ConditionFilter()
    assert cf.normalize_label("Like new") == NormalizedCondition.EXCELLENT
    assert cf.normalize_label("Come nuovo") == NormalizedCondition.EXCELLENT
    assert cf.normalize_label("Wie neu") == NormalizedCondition.EXCELLENT

def test_normalize_good():
    cf = ConditionFilter()
    assert cf.normalize_label("Good") == NormalizedCondition.GOOD
    assert cf.normalize_label("Buono") == NormalizedCondition.GOOD
    assert cf.normalize_label("Gut") == NormalizedCondition.GOOD

def test_normalize_unknown():
    cf = ConditionFilter()
    assert cf.normalize_label("") == NormalizedCondition.UNKNOWN
    assert cf.normalize_label("some random text") == NormalizedCondition.UNKNOWN

def test_normalize_for_parts_feeds_to_exclusion():
    cf = ConditionFilter()
    assert cf.normalize_label("For parts or not working") == NormalizedCondition.EXCLUDED
    assert cf.normalize_label("Per ricambi") == NormalizedCondition.EXCLUDED
