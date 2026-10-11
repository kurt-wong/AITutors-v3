# -*- coding: utf-8 -*-
"""unexplained_loss: pending_review ⊆ ir_ready, must not be subtracted twice."""
from app.domains.source.funnel_recorder import FunnelRecorder


def test_unexplained_loss_does_not_double_count_pending():
    f = FunnelRecorder("pkg")
    f.set("input_units", 10)
    f.set("ir_ready", 6)
    f.set("pending_review", 2)  # subset of ready
    f.set("candidates", 6)
    # 4 units failed/skipped
    for i in range(4):
        f.skip_unit(f"U{i}", "resolver_ir", "stem unresolved")
    d = f.to_dict()
    # old formula: 10 - 6 - 2 - 4 = -2 (wrong)
    # new: 10 - (6+4) = 0
    assert d["unexplained_loss"] == 0, d


def test_unexplained_loss_nonzero_when_no_failure_record():
    f = FunnelRecorder("pkg")
    f.set("input_units", 10)
    f.set("ir_ready", 3)
    d = f.to_dict()
    assert d["unexplained_loss"] == 7


def test_run_identity_in_output():
    f = FunnelRecorder("pkg")
    f.set_run_identity("run-42", {"source_md_sha256": "abc"})
    f.set("input_units", 1)
    d = f.to_dict()
    assert d["run_id"] == "run-42"
    assert d["input_hashes"]["source_md_sha256"] == "abc"
