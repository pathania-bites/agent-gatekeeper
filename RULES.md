# Agent Gatekeeper Rules (Amazon, Online Store)

Rules are checked in this order:

1. Revoked agent -> BLOCK
2. Unregistered agent -> BLOCK
3. Missing or invalid fields (unknown action, no customer, or place order / return / refund without a valid amount) -> BLOCK
4. View order -> ALLOW
5. Place order up to Rs 3,000 -> ALLOW
6. Place order above Rs 3,000 -> ASK CUSTOMER
7. Refund, any amount -> ASK CUSTOMER
8. Return up to Rs 3,000 -> ALLOW, above Rs 3,000 -> ASK CUSTOMER

Limit justification: Rs 3,000 covers a typical everyday basket, so routine shopping flows, while big-ticket items like phones need a human.