#!/usr/bin/env python3
"""
Agent Gatekeeper for Amazon (online store).

A shopper's agent can ask to view an order, place an order, return an item,
or give a refund. This program checks that request against RULES.md, in the
order the rules are written, and answers:

    ALLOW         - the agent may do it
    ASK CUSTOMER  - the customer must confirm first
    BLOCK         - the request is not allowed

The program uses only the Python 3.9 standard library.
"""

import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Files live next to this program so it does not matter where you run it from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_FILE = os.path.join(BASE_DIR, "agents.json")
AUDIT_FILE = os.path.join(BASE_DIR, "audit_log.csv")

# Rs 3,000 is the everyday basket limit from RULES.md.
# Orders and returns up to this amount can go through.
# Anything above it needs the customer to confirm.
LIMIT = 3000.0

# The only actions an agent is allowed to ask for.
KNOWN_ACTIONS = ["view_order", "place_order", "return", "refund"]

# A decision is three pieces of text: the answer, the rule number, and why.
Decision = Tuple[str, int, str]
Agent = Dict[str, str]


def now_text() -> str:
    """Return the current date and time as simple text, for example 2026-11-15 17:11:00."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_agents() -> List[Agent]:
    """Read the agent list from agents.json. If the file is missing, nobody is registered yet."""
    if not os.path.exists(AGENTS_FILE):
        return []
    with open(AGENTS_FILE, "r", encoding="utf-8") as handle:
        agents = json.load(handle)
    return agents


def save_agents(agents: List[Agent]) -> None:
    """Write the full agent list back to agents.json."""
    with open(AGENTS_FILE, "w", encoding="utf-8") as handle:
        json.dump(agents, handle, indent=2)


def find_agent(agents: List[Agent], name: str) -> Optional[Agent]:
    """Find one agent by name. Names must match exactly, apart from extra spaces."""
    clean_name = name.strip()
    for agent in agents:
        if agent["name"] == clean_name:
            return agent
    return None


def clean_action(action: str) -> str:
    """Turn 'Place Order' or 'place-order' into place_order before the rules look at it."""
    return action.strip().lower().replace("-", " ").replace(" ", "_")


def parse_amount(amount_text: str) -> Optional[float]:
    """
    Turn the amount the user typed into a number.

    A valid amount is greater than zero. Blank text, words, zero, and
    negative numbers are not valid. Returns None when the amount is not valid.
    """
    text = amount_text.strip().replace(",", "")
    text = text.replace("Rs.", "").replace("Rs", "").replace("rs.", "").replace("rs", "")
    text = text.strip()
    if text == "":
        return None
    try:
        value = round(float(text), 2)
    except ValueError:
        return None
    if value <= 0:
        return None
    return value


def check_request(customer: str, agent_name: str, action: str, amount_text: str) -> Decision:
    """
    Apply the rules in RULES.md in the order they are written.

    The first rule that matches wins. Later rules are not checked.
    """
    agents = load_agents()
    agent = find_agent(agents, agent_name)
    customer_name = customer.strip()
    action_name = clean_action(action)
    amount = parse_amount(amount_text)

    # Rule 1: Revoked agent -> BLOCK
    # A revoked agent must not do anything, even if the request itself looks fine.
    if agent is not None and agent["status"] == "revoked":
        return ("BLOCK", 1, "This agent has been revoked")

    # Rule 2: Unregistered agent -> BLOCK
    # An unknown name is not an agent we can trust.
    if agent is None:
        return ("BLOCK", 2, "This agent is not registered")

    # Rule 3: Missing or invalid fields -> BLOCK
    # The customer name must be present, the action must be one we know,
    # and place order / return / refund must include an amount above zero.
    # View order does not need an amount.
    needs_amount = action_name in ["place_order", "return", "refund"]
    if customer_name == "" or action_name not in KNOWN_ACTIONS:
        return ("BLOCK", 3, "The customer or the action is missing or invalid")
    if needs_amount and amount is None:
        return ("BLOCK", 3, "Place order, return, and refund need an amount above zero")

    # Rule 4: View order -> ALLOW
    # Looking at an order does not move money, so an active agent may do it.
    if action_name == "view_order":
        return ("ALLOW", 4, "Viewing an order is allowed")

    # Rule 5: Place order up to Rs 3,000 -> ALLOW
    # A normal everyday basket can be placed without asking the customer again.
    if action_name == "place_order" and amount <= LIMIT:
        return ("ALLOW", 5, "Place order up to Rs 3,000 is allowed")

    # Rule 6: Place order above Rs 3,000 -> ASK CUSTOMER
    # A big purchase, such as a phone, needs the customer to confirm.
    if action_name == "place_order" and amount > LIMIT:
        return ("ASK CUSTOMER", 6, "Place order above Rs 3,000 needs the customer to confirm")

    # Rule 7: Refund, any amount -> ASK CUSTOMER
    # Giving money back always needs the customer, even for a small amount.
    if action_name == "refund":
        return ("ASK CUSTOMER", 7, "A refund always needs the customer to confirm")

    # Rule 8: Return up to Rs 3,000 -> ALLOW, above Rs 3,000 -> ASK CUSTOMER
    # A small return can go through. A large return needs the customer to confirm.
    if action_name == "return" and amount <= LIMIT:
        return ("ALLOW", 8, "Return up to Rs 3,000 is allowed")
    if action_name == "return" and amount > LIMIT:
        return ("ASK CUSTOMER", 8, "Return above Rs 3,000 needs the customer to confirm")

    # Every known action is handled above. This line is only a safety net.
    return ("BLOCK", 3, "The customer or the action is missing or invalid")


def log_decision(
    customer: str,
    agent_name: str,
    action: str,
    amount_text: str,
    decision: str,
    rule_number: int,
    reason: str,
) -> None:
    """Append one decision to audit_log.csv. The header row is written once."""
    file_is_new = (not os.path.exists(AUDIT_FILE)) or os.path.getsize(AUDIT_FILE) == 0
    with open(AUDIT_FILE, "a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if file_is_new:
            writer.writerow(
                [
                    "timestamp",
                    "customer",
                    "agent",
                    "action",
                    "amount",
                    "decision",
                    "rule_number",
                    "reason",
                ]
            )
        writer.writerow(
            [
                now_text(),
                customer.strip(),
                agent_name.strip(),
                action.strip(),
                amount_text.strip(),
                decision,
                rule_number,
                reason,
            ]
        )


def register_agent() -> None:
    """Menu option 1. Save a new active agent with the date and time they were registered."""
    name = input("Agent name: ").strip()
    if name == "":
        print("Please enter an agent name.")
        return

    agents = load_agents()
    existing = find_agent(agents, name)
    if existing is not None:
        if existing["status"] == "revoked":
            print("That agent is already registered and has been revoked.")
        else:
            print("That agent is already registered.")
        return

    agents.append(
        {
            "name": name,
            "status": "active",
            "registered_at": now_text(),
            "revoked_at": "",
        }
    )
    save_agents(agents)
    print("Registered " + name + " as an active agent.")


def revoke_agent() -> None:
    """Menu option 2. Mark an agent as revoked and save the date and time."""
    name = input("Agent name to revoke: ").strip()
    if name == "":
        print("Please enter an agent name.")
        return

    agents = load_agents()
    agent = find_agent(agents, name)
    if agent is None:
        print("That agent is not registered.")
        return
    if agent["status"] == "revoked":
        print("That agent was already revoked at " + agent["revoked_at"] + ".")
        return

    agent["status"] = "revoked"
    agent["revoked_at"] = now_text()
    save_agents(agents)
    print("Revoked " + name + " at " + agent["revoked_at"] + ".")


def check_request_from_menu() -> None:
    """Menu option 3. Ask for one request, decide it, print the result, and log it."""
    print("Actions: view_order, place_order, return, refund")
    customer = input("Customer: ")
    agent_name = input("Agent name: ")
    action = input("Action: ")
    amount_text = input("Amount in Rs (press Enter for view_order): ")

    decision, rule_number, reason = check_request(customer, agent_name, action, amount_text)
    log_decision(customer, agent_name, action, amount_text, decision, rule_number, reason)

    print("")
    print("Decision: " + decision)
    print("Rule: " + str(rule_number))
    print("Reason: " + reason)


def show_audit_log() -> None:
    """Menu option 4. Print every decision that has been saved."""
    if not os.path.exists(AUDIT_FILE) or os.path.getsize(AUDIT_FILE) == 0:
        print("No decisions have been logged yet.")
        return

    with open(AUDIT_FILE, "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    if len(rows) <= 1:
        print("No decisions have been logged yet.")
        return

    for row in rows:
        print(" | ".join(row))


def main() -> None:
    """Show the enrolment number, then keep showing the menu until the user exits."""
    print("Enrolment No: 202562997")
    print("Agent Gatekeeper for Amazon")

    while True:
        print("")
        print("1) Register an agent")
        print("2) Revoke an agent")
        print("3) Check a request")
        print("4) Show audit log")
        print("5) Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            register_agent()
        elif choice == "2":
            revoke_agent()
        elif choice == "3":
            check_request_from_menu()
        elif choice == "4":
            show_audit_log()
        elif choice == "5":
            print("Goodbye.")
            break
        else:
            print("Please enter a number from 1 to 5.")


if __name__ == "__main__":
    main()
