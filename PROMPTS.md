# Prompts I gave the coding agent

## Prompt 1 (date: 15 Nov 2026)
Read RULES.md in this folder. Build a simple Python command-line program called Agent Gatekeeper for Amazon (online store) in a file called gatekeeper.py. The code must run on Python 3.9 using only the standard library. Do not use the match statement or the X | Y type hint syntax. Print "Enrolment No: 202562997" when the program starts. A request has: customer, agent name, action (view_order, place_order, return, refund) and amount. The program returns ALLOW, ASK CUSTOMER or BLOCK with the rule number and a reason, applying the rules in RULES.md in exactly the order written there. Store agents in agents.json with name, status (active or revoked), registered_at and revoked_at. Add a menu with: 1) register an agent, 2) revoke an agent (save date and time), 3) check a request, 4) show audit log, 5) exit. Log every decision to audit_log.csv with timestamp, request details, decision and rule number. Keep the code simple, with a comment on each rule, so a beginner can explain it.

## Checked / changed by me (17 Nov 2026)
- I tested a revoked agent (ShopBot) doing view_order and place_order with small amounts. It was blocked by Rule 1 every time, so the revoke check runs before the action and amount rules.
- I left the customer name blank by mistake and found that Rule 3 blocks it.
- My first test run reused an agent I had already revoked on 15 Nov, so results were wrong. I registered fresh agents (ShopBot2, ShopBot3) and re-ran all 6 tests, and all passed.
- I tested a negative amount (-100) for place_order and it was blocked by Rule 3.