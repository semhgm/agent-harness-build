from v9 import Session, withNotice


def test_no_notice_when_clean():
    s = Session()
    assert withNotice(s, "merhaba") == "merhaba"


def test_notice_when_tainted():
    s = Session()
    s.tainted = True
    s.untrusted_sources = ["deneme1.txt"]
    out = withNotice(s, "merhaba")
    assert out.startswith("merhaba")
    assert "[harness]" in out
    assert "deneme1.txt" in out


if __name__ == "__main__":
    test_no_notice_when_clean()
    test_notice_when_tainted()
    print("ok")