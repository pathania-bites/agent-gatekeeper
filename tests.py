#!/usr/bin/env python3
"""
Six checks for Agent Gatekeeper.

Uses gatekeeper.check_request, which is the same decision logic as the menu.
Agent data is written to a temporary file. agents.json and audit_log.csv
are not read or written.

Python 3.9, standard library only.
"""

import json
import os
import tempfile

import gatekeeper

# Temporary agents. They are not the people stored in agents.json.
TEMP_AGENTS = [
    {
        "name": "Active",
        "status": "active",
        "registered_at": "2026-01-01 09:00:00",
        "revoked_at": "",
    },
    {
        "name": "Revoked",
        "status": "revoked",
        "registered_at": "2026-01-01 09:00:00",
        "revoked_at": "2026-01-02 09:00:00",
    },
]

# Case, customer, agent, action, amount, expected decision, expected rule.
CASES = [
    (1, "Rahul", "Active", "view_order", "", "ALLOW", 4),
    (2, "Rahul", "Nobody", "place_order", "500", "BLOCK", 2),
    (3, "Rahul", "Active", "place_order", "8000", "ASK CUSTOMER", 6),
    (4, "Rahul", "Active", "place_order", "1200", "ALLOW", 5),
    (5, "Rahul", "Revoked", "place_order", "500", "BLOCK", 1),
    (6, "Rahul", "Active", "refund", "200", "ASK CUSTOMER", 7),
]


def result_text(decision, rule_number):
    """Turn a decision and a rule number into one column, such as ALLOW Rule 4."""
    return decision + " Rule " + str(rule_number)


def run_cases(cases):
    """
    Point the gatekeeper at a temporary agent file, run every case, then
    put the original file path back. The audit log function is never called.
    """
    original_agents_file = gatekeeper.AGENTS_FILE
    temp_path = None
    outcomes = []
    try:
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        temp_path = handle.name
        json.dump(TEMP_AGENTS, handle)
        handle.close()

        # check_request reads whatever path is in AGENTS_FILE.
        gatekeeper.AGENTS_FILE = temp_path

        for case in cases:
            number, customer, agent_name, action, amount, expected, rule = case
            decision, actual_rule, _reason = gatekeeper.check_request(
                customer, agent_name, action, amount
            )
            expected_text = result_text(expected, rule)
            actual_text = result_text(decision, actual_rule)
            outcomes.append((number, expected_text, actual_text))
    finally:
        gatekeeper.AGENTS_FILE = original_agents_file
        if temp_path is not None and os.path.exists(temp_path):
            os.remove(temp_path)
    return outcomes


def print_report(outcomes):
    """Print the enrolment number, the result table, and how many cases passed."""
    print("Enrolment No: 202562997")

    case_width = 6
    expected_width = 22
    actual_width = 22
    header = (
        "Case".ljust(case_width)
        + "Expected".ljust(expected_width)
        + "Actual".ljust(actual_width)
        + "PASS/FAIL"
    )
    print(header)
    print("-" * len(header))

    passed = 0
    for number, expected_text, actual_text in outcomes:
        status = "PASS" if expected_text == actual_text else "FAIL"
        if status == "PASS":
            passed = passed + 1
        print(
            str(number).ljust(case_width)
            + expected_text.ljust(expected_width)
            + actual_text.ljust(actual_width)
            + status
        )

    print(str(passed) + " passed out of " + str(len(outcomes)))


def main():
    outcomes = run_cases(CASES)
    print_report(outcomes)


if __name__ == "__main__":
    main()
