# Screens Under Review

## Checkout form, shipping address

Message: This field takes a maximum of 30 characters. Shorten the entry and save again.
Placement: directly below the postal code field
Container: inline
Signal: bold text set larger than the field label, icon
Fires: after-field-complete
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none

Message: Please correct the highlighted field. Error code: 502.
Placement: directly below the shipping address block
Container: inline
Signal: bold text set above the address block at a larger size than its labels, icon
Fires: on-blur
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none

## File upload, receipts

Message: This receipt is over the 10 MB limit, which keeps uploads quick on slow connections. Reduce the file size and upload it again.
Placement: directly below the upload control
Container: inline
Signal: bold text below the upload control at a larger size than its caption, icon
Fires: after-field-complete
Predictable mistake: yes
Input on resubmission: not-applicable
Suggested fix: described, names the one available alternative but requires the reader to enter it by hand

Message: Receipts upload as PDF or PNG only, the two formats the expense system can read. Change this file to one of those formats and upload it again, or select a different receipt.
Placement: directly below the upload control
Container: inline
Signal: bold text below the upload control at a larger size than its caption, icon
Fires: on-submit
Predictable mistake: yes
Input on resubmission: not-applicable
Suggested fix: selectable, offers a convert and retry action in place of the message

## Password reset, new password

Message: Choose a password of at least 8 characters, long enough that a guessing attack cannot work through every combination.
Placement: at the top of a long form, requiring the reader to scroll up to see it, though the field itself stays visible on the page
Container: inline
Signal: bold text set larger than the field label, icon
Fires: after-field-complete
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none

Message: This reset link expired an hour after it was sent, so nobody can reuse it from an old message. Request a new link and check the inbox again.
Placement: in a dialog centered on the password reset step, over the new password field it blocks
Container: toast
Signal: bold heading text at the top of the dialog, icon
Fires: on-focus
Predictable mistake: no
Input on resubmission: not-applicable
Suggested fix: selectable, offers a send a new link button in place of the message

## Account settings, username

Message: The last changes were not saved and cannot be recovered. Contact support for assistance.
Placement: directly below the username field
Container: inline
Signal: bold text set larger than the field label, icon
Fires: on-blur
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none
