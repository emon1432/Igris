"""Unit Tests for Action Ledger Cryptographic Chaining."""

import pytest
from igris_protocol.models import RiskTier
from igris_ledger.ledger import ActionLedger, GENESIS_HASH


def test_empty_ledger_integrity():
    ledger = ActionLedger()
    assert ledger.current_height == 0
    assert ledger.latest_hash == GENESIS_HASH
    assert ledger.verify_chain_integrity() is True


def test_append_entries_and_verify_chain():
    ledger = ActionLedger()

    entry1 = ledger.append(
        task_id="task_1",
        tool_name="read_email",
        risk_tier=RiskTier.T0,
        input_parameters={"folder": "INBOX"},
        output_summary="2 emails read",
        timestamp=1000.0,
    )
    assert entry1.index == 0
    assert entry1.prev_hash == GENESIS_HASH
    assert ledger.verify_chain_integrity() is True

    entry2 = ledger.append(
        task_id="task_1",
        tool_name="git_branch_commit",
        risk_tier=RiskTier.T1,
        input_parameters={"branch": "fix-123"},
        output_summary="Committed",
        timestamp=1001.0,
    )
    assert entry2.index == 1
    assert entry2.prev_hash == entry1.entry_hash
    assert ledger.verify_chain_integrity() is True


def test_tampering_detected():
    ledger = ActionLedger()
    ledger.append("task_1", "read_email", RiskTier.T0, {}, "summary 1", timestamp=100.0)
    ledger.append("task_1", "write_file", RiskTier.T1, {}, "summary 2", timestamp=101.0)
    assert ledger.verify_chain_integrity() is True

    # Tamper with historical entry
    tampered_entry = ledger.get_all_entries()[0]
    tampered_entry.output_summary = "TAMPERED SUMMARY"

    assert ledger.verify_chain_integrity() is False

