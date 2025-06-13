from caterminator.functions.categorizer import extract_category


def test_extract_category():
    categories = {"Groceries": {}, "Salary": {}, "Utilities": {}}

    assert extract_category("groceries", categories) == "Groceries"
    assert extract_category("GROCERIES", categories) == "Groceries"
    assert extract_category('"groceries"', categories) == "Groceries"
    assert extract_category("</think>\ngroceries", categories) == "Groceries"
    assert extract_category("unknown", categories) == "to categorize"
