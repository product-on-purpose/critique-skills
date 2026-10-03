# Real-forms review: AC-10 scripted-lane findings on 22 live forms

This report covers AC-10 (real-forms acceptance check) from the N2 critique-forms spec
(docs/internal/release-plans/_unassigned/N2_critique-forms/spec.md). It hand-classifies every
finding the scripted checker produced. The checker is
skills/critique-forms/scripts/checks.py at commit 6c408bb. It ran against 22 saved, real, live
web forms. This report also hand-checks every form for defects the checker should have reported
and did not. The review brief that commissioned this report named 21 forms. The committed
findings directory in fact holds 22 findings files. This report uses all 22 and flags the
discrepancy here, once. The scripted lane covers 18 of the skill's 24 criteria. The 6 judged
criteria are out of scope for this check.
Classifications live in _local/real-forms/classification.json. No copy of any form is committed
to this repository. The saved HTML lives only in the gitignored _local/real-forms directory.

**Outcome: the first run failed the AC-13 gate on one criterion, and the second run passes it.**
On the first run, FORMS-REQUIRED-OPTIONAL fired 3 times and all 3 were false alarms, each caused by
an anti-spam honeypot the checker could not see was hidden. The spec's rule is that such a
criterion is fixed or moved to the judged lane before the paid run. The checker was fixed: it now
skips controls hidden by declared CSS, by a hidden class on the control itself, or by a label
that warns a person off them, and search now outranks phone in the purpose table. The second run,
in the section "Second run, after the hidden-control fix", has 85 findings: 84 correct and 1 false
alarm, and no criterion fails the gate. The sections between record the first run as classified.

## Forms checked

| Slug | Kind | URL | Accessed | SHA-256 |
|---|---|---|---|---|
| bugzilla-mozilla-create | sign-up | https://bugzilla.mozilla.org/createaccount.cgi | 2026-09-30 | 1680b3b81ed7a369ffd4a40eddbb7ff9f228ccfc4299fc2bb546023fd9e95a2e |
| contactform7-contact | contact | https://contactform7.com/contact/ | 2026-09-30 | 14a0e7c45452d2a566402fe41759c301b61e1d08082aad15950b616eb5277595 |
| debian-lists-subscribe | sign-up | https://www.debian.org/MailingLists/subscribe | 2026-09-30 | 403e65d2e2df68ac77f6026626893c2f7e60dfd7b1230357e5a7a5207f84b829 |
| discourse-meta-signup | sign-up | https://meta.discourse.org/signup | 2026-09-30 | 4ef31e640535570df303987ec69ff41d5f06152112b1851f7d79f52a9b6aa967 |
| freebsd-lists-subscribe | sign-up | https://lists.freebsd.org/subscription/freebsd-questions | 2026-09-30 | 425803b16fecda596008e53f3740c81757ec68547b4cf99dfed6cc33ed790190 |
| fsf-contact | contact | https://www.fsf.org/about/contact/ | 2026-09-30 | 1d69d19617b99ab0011191239c90c1f5dae7318f8aa20fda0f755f70c101d9f3 |
| gitlab-signup | sign-up | https://gitlab.com/users/sign_up | 2026-09-30 | fdcdb12773e4b43eea1be5c1c29fb56a64d3fcd2f8ee098043cd3147a9b683ee |
| gnu-mailman-subscribe | sign-up | https://lists.gnu.org/mailman/listinfo/help-gnu-emacs | 2026-09-30 | 76143f805e83d3e003f18455e20d737812850db3cd3f88f26a9815da06ffe7ca |
| govuk-contact | contact | https://www.gov.uk/contact/govuk | 2026-09-30 | 2ba17491cbc0b92f323b89ad729d31522a20308939bdbde21fb14a08b465a85f |
| govuk-find-council | address | https://www.gov.uk/find-local-council | 2026-09-30 | e70362b54c19591fbd2b9e2cec3327dbe6d273a90f82fb8710f885729dc8462d |
| govuk-state-pension-age | profile | https://www.gov.uk/state-pension-age/y | 2026-09-30 | 3d1c4fc8b490c4d56e236f282e64a458e1709bc6212e78ab985a795bd6e15b18 |
| hackernews-login | sign-up | https://news.ycombinator.com/login | 2026-09-30 | e1324f1543a8dd9e91c92868ddc6544dbdb0a8aee9813779640445ba816e5d1d |
| lwn-subscribe | sign-up | https://lwn.net/Login/newaccount | 2026-09-30 | f74ce79bb75fddce789d0e7d7657306b6c7537fd040270d9b9a326550899dc86 |
| mediawiki-create-account | sign-up | https://www.mediawiki.org/w/index.php?title=Special:CreateAccount | 2026-09-30 | 11bb1054e6f1060a3783ab7dcc55ee18a160410afe34e4d31e2ada0b450c6299 |
| openstreetmap-signup | sign-up | https://www.openstreetmap.org/user/new | 2026-09-30 | aa3805818e21a870f4b3c958c2ad3154bf99b5adda549faa865bcda992434987 |
| php-net-account | sign-up | https://www.php.net/git-php.php | 2026-09-30 | eff37445372406bef9d5572f5fa74f1a2bbf1bda8e72c70ca55059a66b0d6112 |
| pypi-register | sign-up | https://pypi.org/account/register/ | 2026-09-30 | d0f3a86209f3e79ccbce862fc65b6bca61ec5e8a3b2140b2b4bb66a5a83bc534 |
| python-org-signup | sign-up | https://www.python.org/accounts/signup/ | 2026-09-30 | 13164c23e938f9632963e47840ecc23e2b814d3c737a819914bbb97d45864eaa |
| register-to-vote | address | https://www.registertovote.service.gov.uk/register-to-vote/start | 2026-09-30 | c0202435b267c2acd423a0762e8dfbecfbc88ee245f8a977a07c6c4a489d424a |
| savannah-register | sign-up | https://savannah.gnu.org/account/register.php | 2026-09-30 | 7ecd12336d65e94dfad27fec7d9483185e4d8161e397195fc13cf803b0ac87d6 |
| wikipedia-create-account | sign-up | https://en.wikipedia.org/w/index.php?title=Special:CreateAccount | 2026-09-30 | ed16c5497113e41e656e9252018e519d9c031ba97012d13644ccd610ae0316f7 |
| wordpress-register | sign-up | https://login.wordpress.org/register | 2026-09-30 | fffa3569ce29f0d788db39544b9734a7dc4f8734f15d410846c731f613aa8c39 |

## Results per criterion (first run)

The checker produced 93 findings across these 22 forms. Fired counts below sum to 93. The gate
column applies AC-13 (the false-alarm gate a criterion must clear before a paid benchmark run).
A criterion with 3 or more findings fails that gate when its false alarms outnumber its correct
findings. It passes when they do not. Below 3 findings the gate is inconclusive, since that few
cases cannot support a verdict either way.

| Criterion | Fired | Correct | False alarms | Misses | Gate |
|---|---|---|---|---|---|
| FORMS-INPUT-TYPE | 14 | 12 | 2 | 3 | pass |
| FORMS-NUMERIC-INPUTMODE | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-AUTOCOMPLETE | 37 | 34 | 3 | 5 | pass |
| FORMS-AUTOCORRECT | 23 | 21 | 2 | 4 | pass |
| FORMS-PLACEHOLDER-INSTRUCTION | 1 | 1 | 0 | 0 | inconclusive |
| FORMS-REQUIRED-OPTIONAL | 3 | 0 | 3 | 0 | FAIL |
| FORMS-SPLIT-ENTITY | 1 | 0 | 1 | 0 | inconclusive |
| FORMS-FIELD-WIDTH | 1 | 1 | 0 | 0 | inconclusive |
| FORMS-FORMAT-TOLERANCE | 2 | 2 | 0 | 0 | inconclusive |
| FORMS-PASSWORD-RULES | 1 | 1 | 0 | 0 | inconclusive |
| FORMS-CONFIRM-PASSWORD | 6 | 6 | 0 | 2 | pass |
| FORMS-ACTION-LABEL | 3 | 3 | 0 | 0 | pass |
| FORMS-RESET-BUTTON | 1 | 1 | 0 | 0 | inconclusive |
| FORMS-INPUT-FONT-SIZE | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-OPTION-CONTROL | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-DATE-SELECTS | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-PHONE-REASON | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-ADDRESS-FORMAT | 0 | 0 | 0 | 0 | inconclusive |

FORMS-REQUIRED-OPTIONAL is the one criterion that fails the AC-13 gate. It fired 3 times on a real
form. Each time, it fired on a control that is not a real field a person fills in. One is a
never-submitted decoy input with no name attribute, on bugzilla-mozilla-create. Two are honeypot
inputs meant to trap automated submissions, on gitlab-signup and python-org-signup. Zero of its
three firings were correct.

## Second run, after the hidden-control fix

The fix changed two things in checks.py, and FORMS.md now states both. First, a control is skipped
when the artifact's own CSS hides it or an ancestor (display none, visibility hidden, opacity 0, a
width and height of 0, or a left or top of -1000 pixels or less), when the control itself carries
a class named hidden, hide or d-none or ending in -hidden or _hidden, or when its label tells a
person to leave it blank or ignore it. Second, search now outranks email and phone in the purpose
table, so a box called mobile search reads as a search.

A first version also read hidden classes on ancestors. It cost four correct findings: the
bugzilla-mozilla-create login popup and the govuk-contact conditional panel each hide a container
of real fields until a click. The class rule was narrowed to the control itself, and the four
findings returned.

Every first-run finding that disappeared had been classified a false alarm, and no correct finding
was lost. Four findings are new or changed, and each was classified by hand:

- pypi-register `#mobile-search`, FORMS-INPUT-TYPE: now read as a search box declared type=text,
  which the test flags. Correct.
- python-org-signup `#id_username`, FORMS-AUTOCORRECT: severity 3 falls to 2, because the honeypot
  no longer counts toward recurrence. This matches the first run's severity by test. Correct.
- gitlab-signup `#new_user_first_name`, FORMS-SPLIT-ENTITY: First name and Last name split one name,
  and the honeypot no longer joins the run. Correct.
- gitlab-signup, FORMS-REQUIRED-OPTIONAL, at the password control: a false alarm. The control is a
  script mount point, an input with no name, id or type that carries data-name and
  data-required=true. GitLab's script replaces it with the real password field, which is required,
  so the form has no optional field in fact.

| Criterion | Fired | Correct | False alarms | Misses | Gate |
|---|---|---|---|---|---|
| FORMS-ACTION-LABEL | 3 | 3 | 0 | 0 | pass |
| FORMS-ADDRESS-FORMAT | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-AUTOCOMPLETE | 34 | 34 | 0 | 5 | pass |
| FORMS-AUTOCORRECT | 21 | 21 | 0 | 4 | pass |
| FORMS-CONFIRM-PASSWORD | 6 | 6 | 0 | 2 | pass |
| FORMS-DATE-SELECTS | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-FIELD-WIDTH | 1 | 1 | 0 | 0 | inconclusive |
| FORMS-FORMAT-TOLERANCE | 2 | 2 | 0 | 0 | inconclusive |
| FORMS-INPUT-FONT-SIZE | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-INPUT-TYPE | 13 | 13 | 0 | 3 | pass |
| FORMS-NUMERIC-INPUTMODE | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-OPTION-CONTROL | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-PASSWORD-RULES | 1 | 1 | 0 | 0 | inconclusive |
| FORMS-PHONE-REASON | 0 | 0 | 0 | 0 | inconclusive |
| FORMS-PLACEHOLDER-INSTRUCTION | 1 | 1 | 0 | 0 | inconclusive |
| FORMS-REQUIRED-OPTIONAL | 1 | 0 | 1 | 0 | inconclusive |
| FORMS-RESET-BUTTON | 1 | 1 | 0 | 0 | inconclusive |
| FORMS-SPLIT-ENTITY | 1 | 1 | 0 | 0 | inconclusive |

Misses are unchanged from the first run, because the fix only removes controls from view.

**FORMS-REQUIRED-OPTIONAL clears the gate as inconclusive, and that verdict deserves a caveat.**
Across both runs it fired four times on real forms and was never correct. Each firing came from a
control that is not a field a person fills in, which the form-level test then counted as the
form's optional field. The criterion is untested on real forms rather than shown to work, and the
paid run's figures for it come from the generated corpus alone.

## False alarms (first run)

Eleven findings are false alarms. They group into two causes.

**Honeypot or decoy fields the checker counted as real, nine findings.** gitlab-signup's
FORMS-AUTOCOMPLETE, FORMS-AUTOCORRECT, FORMS-REQUIRED-OPTIONAL, and FORMS-SPLIT-ENTITY findings
all point at one control. Its id and name are both firstname. Its label text reads "If you are
human, please ignore this field." Its wrapping div carries a page-level style block. That block
sets position:absolute !important; top:-9999px; left:-9999px on class firstname_1790826273, so
the field never appears on screen. Its own garbage autocomplete value is the anti-bot device
working as designed, not a missing token.

python-org-signup's FORMS-AUTOCOMPLETE, FORMS-AUTOCORRECT, FORMS-INPUT-TYPE, and
FORMS-REQUIRED-OPTIONAL findings all point at one honeypot input. Its name is email_body_text.
Its label reads "leave this field blank to prove your humanity." Its wrapping div carries an
inline style of opacity:0; position:absolute; top:0; left:0; height:0; width:0; z-index:-1.

bugzilla-mozilla-create's FORMS-REQUIRED-OPTIONAL finding points at
input#Bugzilla_password_dummy_top. This is a legacy placeholder-emulation decoy. It has no name
attribute, so it is never submitted. It carries class bz_default_hidden among others.

**A purpose misread from a coincidentally matching cue word, two findings.** pypi-register's
FORMS-AUTOCOMPLETE and FORMS-INPUT-TYPE findings both point at id=mobile-search. This is the
mobile-layout twin of the page's desktop search box, id=search, which the checker read correctly.
The id contains the word "mobile." The purpose table ranks "mobile" above "search." So the
checker reads this field as a phone number field instead of a search field.

Full list of the 11 false alarms, with form, location, and cause, is in classification.json.

## Misses

Fourteen misses were found by hand-applying each scripted criterion's operational test to every
visible control in all 22 forms. A control counts as a miss under either of two conditions. One:
something outside the four signals the heuristic reads names its purpose plainly. That something
can be a title attribute, an aria-label, a role, or a table caption. It can also be a data-*
attribute, an adjacent paired field, or surrounding markup such as a container id or button text.
Two: a word inside one of the four signals names the purpose plainly. That word is simply absent
from the purpose or autocomplete cue tables. A person reads such a word as the field's
purpose without effort. The heuristic does not, because the word is missing from its vocabulary.
A defect the operational test would not flag either way is not a miss, even where it looks like a
real problem. These 14 group into three patterns, plus one miss outside them.

**Old table markup with no label element on the page, six misses.** gnu-mailman-subscribe's
pw-conf field has a caption, "Reenter password to confirm:". That caption sits in a table cell,
not a label element. FORMS-CONFIRM-PASSWORD never sees it, and so never fires. php-net-account's
id field has the same problem: its caption, "User ID:", also sits in a table cell. It is missed
by both FORMS-AUTOCOMPLETE and FORMS-AUTOCORRECT. savannah-register's form_pw2 is missed by
FORMS-CONFIRM-PASSWORD, and its form_loginname is missed by both FORMS-AUTOCOMPLETE and
FORMS-AUTOCORRECT. All three of these pages have zero label elements anywhere. The purpose and
confirm-pairing signals that depend on label text have nothing to read on any of them.

**A compound identifier that will not split into a cue word, two misses.**
bugzilla-mozilla-create's id=quicksearch_top carries role=searchbox, aria-label "Search Terms,"
and placeholder "Search Bugs." FORMS-INPUT-TYPE misses it anyway, because "quicksearch" is one
unbroken word that never matches the search cue. fsf-contact's name=SearchableText, title "Search
Site," is missed by the same test for the same reason.

**A single-letter or domain-synonym name or label outside the cue vocabulary, five misses.**
debian-lists-subscribe's name=P is missed by FORMS-INPUT-TYPE. The name is one letter, so no word
split can help it. The surrounding markup still names the field a search box, three separate
ways. A container div carries id searchbox. The form action points at a search CGI endpoint. A
submit button is labeled Search. None of those three signals are among the four the heuristic reads.
lwn-subscribe's two login-form fields, #f1 (label "Account name") and #uc (label "User:"), are
each missed by both FORMS-AUTOCOMPLETE and FORMS-AUTOCORRECT. The username cue list does not
include the phrase "account name" or the bare word "user." These two are the softest misses in
this review. A maintainer could reasonably treat either one as outside the heuristic's intended
reach, rather than as a defect to fix.

**One miss outside these patterns.** gitlab-signup's password field is assembled by JavaScript.
The saved static markup exposes only data-name="new_user[password]" and
data-autocomplete="new-password", on a real input element. It has no name, id, type, or
autocomplete attribute yet. FORMS-AUTOCOMPLETE would flag the missing token if the checker could
read it. The checker reads real attributes only, and this input does not have any yet.

Full list of the 14 misses, with form, control, and the operational-test clause each one meets,
is in classification.json.

## Severity disagreements (first run)

One finding's severity changes under hand-verification. python-org-signup's FORMS-AUTOCORRECT
finding on #id_username was reported at severity 3. That severity rests on a count of two flagged
fields in the form. One of those two fields is the email_body_text honeypot. Once that honeypot
is excluded as not a real control, one flagged field remains. severity_by_test is 2.

The rule applied throughout this review: severity_by_test is what the operational test, as
written, gives when applied to the real controls in a form. Removing a false alarm from a
recurrence count is applying the test correctly, so severity drops when a false alarm is excluded.
Adding a miss to a count would apply a different, improved test, not the test as written. So a
miss never raises another finding's severity_by_test.

One place this rule has a visible consequence, without changing a reported number, is
savannah-register. Its form_email FORMS-AUTOCORRECT finding is reported, and stays, at severity 2,
based on one flagged field. form_loginname is a miss in this same form, for the same criterion.
If form_loginname were correctly read as a username field, the flagged count in this form would
become two. That would raise form_email's severity to 3, under the checker's own severity rule.
The finding stays at severity 2 as reported. This note is the record of what a fixed heuristic
would change.

## What this does not show

Four correct findings sit on controls that were hidden by an external stylesheet class at the
moment the page was saved. None of the four is visible by default. bugzilla-mozilla-create's
#Bugzilla_login_top and #Bugzilla_password_top sit inside a "Log In" popup, under class
bz_default_hidden, revealed by a JS click handler. bugzilla-mozilla-create's loginname field, at
line 243, sits inside a "Forgot Password" popup, under the same class. govuk-contact's #link
field sits inside a GOV.UK Design System conditional-reveal panel, under class
govuk-radios__conditional--hidden, shown only once a sibling radio button is selected. All four
are counted correct. Each is a real control a person reaches through ordinary use of the page.
The missing autocomplete token, or the wrong input type, is a real defect for that person once
the control becomes visible. A stricter reading is possible: treat "visible" as "visible at page
load, with no prior interaction." Under that reading all four become false alarms instead.
FORMS-AUTOCOMPLETE would then stand at 31 correct and 6 false alarms. FORMS-INPUT-TYPE would
stand at 11 correct and 3 false alarms. Both criteria still pass the AC-13 gate under either
reading. Separately, govuk-contact's #link label reads "Enter URL or name of page." So the field
accepts plain page names, not only URLs. A browser's native validation under the suggested
type=url would reject a bare page name. The suggested fix fully fits only the URL half of what
this field accepts.

Every inline style block in all 22 saved pages was read by hand for font-size rules under 16px.
This search covered input, textarea, and select selectors, including descendant selectors and
rules inside media queries, both of which the checker's own stylesheet reader discards. None were
found. freebsd-lists-subscribe's only sub-16px font-size rule applies to a button element, not to
a text-entry control, so it is not a miss. FORMS-INPUT-FONT-SIZE and FORMS-FIELD-WIDTH both
depend on declared CSS. Only inline style attributes and inline style blocks were available for
this review. None of the 22 pages saved their external stylesheets. Any font-size or width rule
declared there is outside what this review, or the checker, could see.

The checker's hiding check, _is_hidden, recognizes two things. One is the hidden attribute, or
aria-hidden=true. The other is an inline style attribute setting display:none or
visibility:hidden, checked by walking up the ancestor chain. It does not read any class selector
in a style block or an external stylesheet. The gitlab-signup honeypot is hidden by a page-level
style block targeting a generated class name. The four disclosure-widget fields above are hidden
by classes defined in external stylesheets not saved. Both kinds are equally invisible to it.
This holds whether the hidden control is a decoy or a legitimate field. This is a separate gap
from python-org-signup's honeypot. That honeypot is hidden by an inline style attribute, which
_is_hidden does read, but the attribute sets opacity, position, and zero width and height.
_is_hidden checks only display and visibility, not those properties. Both gaps are implementation
scope limits in how hiding is detected. Neither is a failure to apply FORMS.md as written:
FORMS.md's own text defines hiding only in terms of display and visibility. The second run closes
both gaps for CSS the artifact itself declares; external stylesheets remain unread.

These 22 forms skew toward open-source project sign-up and mailing-list pages, and toward UK
government services. No forms from large commercial e-commerce, banking, or healthcare sites are
included. Several forms produced zero findings in this sample: govuk-find-council,
govuk-state-pension-age, register-to-vote, discourse-meta-signup, and hackernews-login. That does
not mean these forms have no defects a scripted criterion could find. It means only that none
were present in the controls this checker evaluated. Twelve of the eighteen scripted criteria
fired fewer than 3 times across all 22 forms: six fired zero times and six fired once or twice.
Each of these 12 is marked inconclusive for the AC-13 gate. Of the remaining six, five pass and
one, FORMS-REQUIRED-OPTIONAL, fails. A paid
benchmark run aimed at those criteria would need a form sample built to contain the specific field
types they check. General-purpose sign-up and contact forms rarely contain house numbers,
one-time codes, date-of-birth select triples, and the like.
