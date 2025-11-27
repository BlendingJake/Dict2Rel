from dict2rel import dict2rel, rel2dict

EXAMPLE = {
    "name": {
        "first": "John",
        "last": "Smith",
        "suffixes": [
            "MD",
            "JD"
        ]
    },
    "phones": [
        {
            "country": "USA",
            "number": "1234567890",
        },
        {
            "country": "ESP",
            "number": "987654321"
        }
    ],
    "matrix": [
        [1, 2],
        [3, 4]
    ]
}


def test_basic():
    """Test basic JSON -> tables"""
    tables = dict2rel([EXAMPLE], lambda x: x)
    assert len(tables) == 4

    assert "*" in tables
    assert len(tables["*"]) == 1
    assert tables["*"][0]["name.first"] == EXAMPLE["name"]["first"]

    assert "*.name.suffixes" in tables
    assert "_value" in tables["*.name.suffixes"][0]


def test_to_tables_and_back():
    """Test JSON -> tables -> JSON"""
    tables = dict2rel([EXAMPLE], lambda x: x)
    og = rel2dict(tables)

    assert og == [EXAMPLE]
