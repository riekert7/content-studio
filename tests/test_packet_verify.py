import pytest
import json

from content_studio.cli import main
from content_studio.packet import build_packet
from content_studio.verify import CRITERIA, verify_marks


def opt(i, **kw):
    return {"id": i, "title": f"Title {i}", "hook": f"hook line {i}", "beats": f"beats for {i}",
            "send_reason": f"send {i}", "out_there": False, "recommended": False, **kw}


EVIDENCE = "Three creators cut to the mug in the first second."


def test_packet_strips_recommendation():
    packet, _ = build_packet([opt("a", recommended=True, send_reason="our pick: this one"), opt("b")], EVIDENCE)
    assert "our pick" not in packet.lower() and "recommend" not in packet.lower()


def test_packet_shuffles_deterministically():
    options = [opt(c) for c in "abcdef"]
    p1, m1 = build_packet(options, EVIDENCE, seed=3)
    p2, m2 = build_packet(options, EVIDENCE, seed=3)
    assert (p1, m1) == (p2, m2) and sorted(m1.values()) == list("abcdef") and sorted(m1) == list("ABCDEF")
    assert p1.index(EVIDENCE) < p1.index("## Option A")


def marks(label, score, quote="", n=6, **over):
    scores = {c: score for c in CRITERIA}
    scores.update(over)
    return {"option": label, "scores": scores, "quotes": {c: quote for c in CRITERIA if scores[c] < 4}}


PACKET = "hook line A is a number. beats for A and   a\nreal incident."


def test_valid_quote_counts():
    m = marks("A", 4, "hook line A is a number", hook=2)
    m["quotes"]["hook"] = "hook line A is a number"
    r = verify_marks(PACKET, [m])[0]
    assert r["total"] == 4 * 5 + 2 and r["rejected"] == []


def test_invented_quote_rejected_counts_as_4():
    m = marks("A", 4, hook=2)
    m["quotes"]["hook"] = "this text is not in the packet"
    r = verify_marks(PACKET, [m])[0]
    assert r["rejected"] == ["hook"] and r["total"] == 24


def test_missing_quote_rejected():
    m = marks("A", 4, hook=2)
    assert verify_marks(PACKET, [m])[0]["rejected"] == ["hook"]


def test_quote_whitespace_normalised():
    m = marks("A", 4, rules=3)
    m["quotes"]["rules"] = "beats for A and a real incident"
    assert verify_marks(PACKET, [m])[0]["rejected"] == []


def three(label, q):
    m = marks(label, 3, q)
    return m


def test_dropped_under_18():
    q = "hook line A"
    m = three("A", q)
    assert verify_marks(PACKET, [m])[0]["total"] == 18 and not verify_marks(PACKET, [m])[0]["dropped"]
    m["scores"]["hook"] = 2
    m["quotes"]["hook"] = q
    r = verify_marks(PACKET, [m])[0]
    assert r["total"] == 17 and r["dropped"]


def test_any_1_drops():
    m = marks("A", 5, hook=1)
    m["quotes"]["hook"] = "hook line A"
    assert verify_marks(PACKET, [m])[0]["dropped"]


def test_out_there_never_dropped():
    m = marks("A", 2, "hook line A")
    r = verify_marks(PACKET, [m], out_there={"A"})[0]
    assert r["dropped"] is False and r["flag"] == "below threshold, your call"


def test_missing_criterion_is_malformed():
    import pytest
    with pytest.raises(ValueError):
        verify_marks(PACKET, [{"option": "A", "scores": {"hook": 5}, "quotes": {}}])


def run(tmp_path, marks_obj, *extra):
    pk, mk = tmp_path / "packet.md", tmp_path / "marks.json"
    pk.write_text(PACKET)
    mk.write_text(marks_obj if isinstance(marks_obj, str) else json.dumps(marks_obj))
    return main(["verify", "--packet", str(pk), "--marks", str(mk), *extra])


def test_all_dropped_exit_3(tmp_path, capsys):
    m = marks("A", 2, "hook line A")
    assert run(tmp_path, [m]) == 3
    assert json.loads(capsys.readouterr().out)[0]["dropped"] is True


def test_survivor_exit_0(tmp_path):
    assert run(tmp_path, [marks("A", 4)]) == 0


def test_malformed_marks_exit_2(tmp_path, capsys):
    assert run(tmp_path, "{not json") == 2
    assert "cs verify" in capsys.readouterr().err


def test_marks_wrong_shape_exit_2(tmp_path, capsys):
    assert run(tmp_path, {"option": "A"}) == 2
    assert "cs verify" in capsys.readouterr().err


def test_out_there_flag_cli(tmp_path):
    assert run(tmp_path, [marks("A", 2, "hook line A")], "--out-there", "A") == 0


def test_packet_cli_writes_map(tmp_path):
    (tmp_path / "options.json").write_text(json.dumps([opt("a"), opt("b")]))
    (tmp_path / "evidence.md").write_text(EVIDENCE)
    out = tmp_path / "packet.md"
    assert main(["packet", "--options", str(tmp_path / "options.json"), "--evidence", str(tmp_path / "evidence.md"),
                 "--out", str(out), "--seed", "1"]) == 0
    assert out.exists() and sorted(json.loads((tmp_path / "packet.map.json").read_text()).values()) == ["a", "b"]


def test_packet_cli_bad_options_exit_2(tmp_path, capsys):
    (tmp_path / "o.json").write_text("{}")
    (tmp_path / "e.md").write_text("x")
    assert main(["packet", "--options", str(tmp_path / "o.json"), "--evidence", str(tmp_path / "e.md"),
                 "--out", str(tmp_path / "p.md")]) == 2
    assert "cs packet" in capsys.readouterr().err


def test_marks_must_cover_each_packet_option_once():
    packet = "# Options\n\n## Option A\nx\n\n## Option B\ny\n"
    with pytest.raises(ValueError, match="exactly once"):
        verify_marks(packet, [marks("A", 4)])
    with pytest.raises(ValueError, match="exactly once"):
        verify_marks(packet, [marks("A", 4), marks("A", 4)])
    assert len(verify_marks(packet, [marks("A", 4), marks("B", 4)])) == 2


def test_one_letter_quote_does_not_save_a_low_score():
    m = marks("A", 4, "a", hook=2)
    m["quotes"]["hook"] = "a"
    assert verify_marks(PACKET, [m])[0]["rejected"] == ["hook"]
