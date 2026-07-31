# Screens Under Review

## Two-factor setup, verification code

Message: Verification codes are 6 digits long, and this one has 5. Check the message again and enter all six.
Placement: directly below the verification code field
Container: inline
Signal: bold text set larger than the field label, icon
Fires: on-blur
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none

Message: This verification code expired 10 minutes after it was sent, which stops an intercepted code from being reused later. Request a new code and enter it here.
Placement: directly below the verification code field
Container: inline
Signal: bold text set larger than the field label, icon
Fires: on-submit
Predictable mistake: no
Input on resubmission: preserved
Suggested fix: selectable, offers a resend code button in place of the message

## Billing, promo code

Message: This promo code ended on 30 June. Enter a current code, or continue without one.
Placement: directly below the promo code field
Container: inline
Signal: bold text set larger than the field label, icon
Fires: on-blur
Predictable mistake: no
Input on resubmission: preserved
Suggested fix: none

Message: This promo code applies to annual plans, and the selected plan is monthly. Change the plan to annual, or remove the code.
Placement: directly below the promo code field
Container: inline
Signal: bold text set larger than the field label, icon
Fires: on-blur
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none
