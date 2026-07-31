---
mode: explanation
---
# Why we chose event sourcing for the order pipeline

The order pipeline used to update a single row per order in place, so the only record of an order's
history was whatever the current row happened to say. Diagnosing a disputed refund meant reading
support tickets and log lines, never the order record itself, since the record itself had already
been overwritten several times by the time anyone went looking.

Event sourcing keeps every state change as its own immutable event, appended to a log rather than
overwritten in place. An order's current state is a read model derived from replaying that log, not
the source of truth itself. This preserves the full history of every order, which is the property the
old design could not offer at any cost, and it decouples the write path from however many read models
downstream services eventually need.

To migrate an existing service onto this pattern:

1. Duplicate the events table so the new consumer can replay history without touching production traffic.
2. Point the new consumer at the duplicated table and let it build its own read model from scratch.
3. Cut traffic over to the new consumer once its read model matches the old one on a full comparison pass.

The tradeoff is storage growth, since nothing is ever deleted, only superseded by a later event. Most
teams accept that cost once they have needed the audit trail even once.
