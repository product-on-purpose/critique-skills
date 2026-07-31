---
mode: reference
---

# Alert rule fields reference

## timeout

The timeout field takes a duration in milliseconds, and the validator rejects any value below 1000.

Leaving this field at its default is the right choice for most teams, and raising it is worth doing only when a specific integration needs the extra room.

## retries

The retries field takes an integer from 0 to 10, and it defaults to 3.

## logging

The logging field accepts one of debug, info, warn, or error, and the default value is info.

## Related pages

- Metric catalog reference
- Notification channel reference
- Webhook delivery reference
- Escalation policy reference
- Time window reference
- Retry backoff reference
- Alert rule schema
- Rate limit reference
- Delivery status codes
