import pathlib

PKG = pathlib.Path(__file__).parents[1] / "chatbot_tester"
FORBIDDEN = ("vuscom", "euris", "vicky", "neta", "salesforce", "responsa")


def test_no_company_or_target_names_in_the_package():
    for f in list(PKG.rglob("*.py")) + list(PKG.rglob("*.yaml")):
        low = f.read_text(encoding="utf-8").lower()
        for w in FORBIDDEN:
            assert w not in low, (f.name, w)
