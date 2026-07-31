---
mode: reference
---

# Webhook delivery reference

## endpoint_url

The endpoint_url field accepts an HTTPS URL that receives the webhook payload for each triggered alert.

## signing_secret

The signing_secret field accepts a string used to verify the payload signature on receipt.

## retry_policy

The retry_policy field accepts one of none, linear, or exponential, and the default value is exponential.
