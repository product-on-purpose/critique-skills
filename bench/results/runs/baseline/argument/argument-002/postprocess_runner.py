import sys
sys.path.insert(0, r'E:\Projects\product-on-purpose\critique-skills')

from bench.baseline.postprocess import postprocess
import json

raw_response = r'''Location: "Circulation Trends" section, first paragraph
Evidence: "It seems that the consortium''s circulation team reviews monthly checkout volume after each fiscal period."
Problem: The opening claim is heavily hedged with "seems," which undermines the credibility of factual information about the consortium''s practices.
Fix: Replace "It seems that" with "The consortium''s circulation team reviews" to state the claim directly.

Location: "Circulation Trends" section, second paragraph
Evidence: "Possibly, the consortium''s circulation team audits monthly checkout volume on the first of every month."
Problem: The paragraph begins with "Possibly," which presents a procedural fact as speculative rather than established.
Fix: Remove "Possibly," and state the auditing practice as fact: "The consortium''s circulation team audits monthly checkout volume on the first of every month."

Location: "What the Pilot Showed" section
Evidence: "Ending overdue fines is plainly the better path for the consortium, and delaying the change would only cost every branch more."
Problem: This statement asserts a strong conclusion as self-evident without sufficient evidence provided yet in the recommendation.
Fix: Revise to "The pilot results suggest ending overdue fines is the better path for the consortium, as delaying the change would impose ongoing costs to each branch."

Location: "What the Pilot Showed" section, survey claim
Evidence: "Arguably, a parallel patron survey found that self-reported avoidance of the library due to fear of fines dropped from 20 percent of respondents before the pilot to 3 percent after it"
Problem: The word "Arguably" weakens a specific statistical claim that should either be stated confidently or explained with caveats about methodology.
Fix: Replace "Arguably, a parallel patron survey found" with "A parallel patron survey found" and add a note about survey limitations if uncertainty is warranted.

Location: "Why the Pilot Result Applies Systemwide" section, first paragraph
Evidence: "In a somewhat qualified way, removing the financial penalty for late returns predictably increases both on-time return rates and overall program participation"
Problem: The phrase "In a somewhat qualified way" is vague and undermines the causal claim without specifying what the qualification is.
Fix: Either remove the qualifier and state the relationship directly, or replace it with specific limitations: "Removing the financial penalty for late returns generally increases both on-time return rates and overall program participation, though effects vary by system."

Location: "Why the Pilot Result Applies Systemwide" section, second paragraph
Evidence: "In a somewhat qualified way, this relationship is documented in the Tri-County Library Data Cooperative''s 2023 fines-elimination research brief, which reviewed return-rate data from fourteen library systems that eliminated fines between 2017 and 2022."
Problem: The citation is vague, lacking publisher information, and the repeated hedging phrase weakens the authority of the source.
Fix: Provide a full citation including author, publication details, or DOI, and remove "In a somewhat qualified way" to state the reference clearly.

Location: "Addressing the Revenue Concern" section
Evidence: "This tends to hold: a skeptic on the board points to overdue fines as a source of materials-replacement funding"
Problem: The phrase "This tends to hold" is vague and does not clearly communicate what relationship is being asserted about the financial argument.
Fix: Replace with a clear statement: "However, the board''s concern about lost fine revenue is mitigated by evidence showing that:"

Location: "Addressing the Revenue Concern" section, financial claim
Evidence: "It might be that consortium finance records show fine revenue covered under 2 percent of the annual materials budget over the last three fiscal years"
Problem: The phrase "It might be that" presents actual financial data as speculative rather than verifiable fact.
Fix: Replace with: "Consortium finance records show that fine revenue covered under 2 percent of the annual materials budget over the last three fiscal years"
'''

result = postprocess(
    raw_response,
    artifact='bench/results/staging/argument/argument-002.md',
    artifact_sha256='0322bc2ebeb48318c56473186a8cb1f1e78d8667b99cfaf75ee7bb84f82fcfa2',
    model='claude-haiku-4-5-20251001',
    timestamp='2026-07-31T20:41:41Z'
)

output_path = r'E:\Projects\product-on-purpose\critique-skills\bench\results\runs\baseline\argument\argument-002\haiku-r2.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
    
print(f"Envelope written to: {output_path}")
print(f"Findings count: {len(result['findings'])}")
print(f"Gate: {result['summary']['gate']}")
