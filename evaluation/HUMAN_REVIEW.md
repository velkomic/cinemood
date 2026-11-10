# Owner review and requested follow-ups — 2026-11-10

The owner reviewed all 20 cases in `RESULTS.md`. The comments below summarize the
feedback, preserving the distinction between recommendation relevance, generated
wording, and operational failures. No numeric human score is inferred from these
qualitative comments, and the historical agent proposal is not relabelled as a
human pass.

| Case | Owner assessment | Requested follow-up |
| --- | --- | --- |
| 1 | Recommendations look fine. | More natural, simpler explanation; remove generic “fit is not perfect” caveats. |
| 2 | Recommendations correct. | Same explanation wording concern. |
| 3 | Good recommendations. | Investigate discarded/unavailable explanation, also seen in case 1. |
| 4 | Looks good. | None. |
| 5 | Nice recommendations. | Investigate unavailable explanation. |
| 6 | Looks good. | None. |
| 7 | Good. | None. |
| 8 | Good. | None. |
| 9 | Explanation problem. | Investigate unavailable explanation. |
| 10 | Good; two results are appropriate for a niche request. | Keep fewer than three when that is all the catalog supports. |
| 11 | Recommendations very good. | Investigate all three unavailable explanations. |
| 12 | Looks good. | None. |
| 13 | Looks fine; The Green Mile as comforting is a stretch, but possible. | Retain qualified mood interpretation without generic boilerplate. |
| 14 | Correctly acknowledges missing cast information. | Actor metadata could be useful after the MVP; not requested as an MVP feature. |
| 15–18 | Looks fine overall. | No explicit change to the conflicting-year policy requested. |
| 19 | Should allow English or French. | Support a list of original languages with OR semantics. |
| 20 | Looks good. | None. |

Case 18's original predefined expectation was clarification for reversed years;
the stored response reordered them. The owner's overall acceptance of the shown
result is recorded, while that historical expectation mismatch remains visible.
The conflicting-year policy is unchanged by these follow-ups.

Case 19 is an explicit product refinement. The original 20-case request file and
captures remain unchanged. The new request interpretation uses
`original_languages: ["en", "fr"]`, with an empty list meaning unrestricted. Each
movie still has one original language in PostgreSQL. Other restrictions and
explicit exclusions apply alongside the language list. A language relaxation
removes the whole list only after selection; other suggestions retain it.

## Verification scope fixed before follow-up calls

`feedback-requests-2026-11-10.json` contains nine targeted cases: 1, 2, 3, 5, 7, 9,
11, 14 and 19. The prompts are unchanged. Case 19's expected outcome explicitly
reflects the owner's language-list refinement. All nine expect completed,
grounded explanations in this sample and direct wording without generic fit
verdicts. This targeted sample is supplementary verification, not a replacement
for the original full evaluation or a new human-reviewed score.

## Diagnosis evidence

- One rerun of case 11 completed all three explanations, confirming the symptom
  is intermittent rather than an empty-catalog problem.
- A bounded five-case REST loop reproduced rejection in cases 3 and 5. The
  smallest live reproduction was one selected movie, Lost in Translation.
- Tagged diagnostics in a temporary isolated app recorded a successful `stop`
  finish and the correct movie ID, but generated evidence began `The young, ...`
  while the stored overview contained `the young, ...`. Rejecting the complete
  explanation for that case-only difference reproduced the reported symptom.
- A deterministic REST regression with fictional licensed fixtures reproduced
  the same capitalization-only rejection before the validation change. Evidence
  normalization alone improved that case, but the nine-case follow-up still
  captured two rejected outputs; those failures remain in its raw artifact.

Further minimized diagnosis found another completed response supplying five
evidence strings, including genre names (`Comedy`, `Fantasy`, `Romance`), where
the output contract allowed at most three overview quotes. This is not a transport
or catalog failure: unconstrained generation was producing unusable citations.

The final change uses strict provider JSON Schema with a per-movie ID enum,
1–3 numeric references restricted to numbered overview excerpts, and application
validation of the same bounds. Public `evidence` strings are resolved by the
server from those excerpts. The public stream/event format, source-selected IDs,
card preservation, cancellation and error behavior remain unchanged. This
supersedes the interim case-normalization approach, rather than allowing model
paraphrases or genre names to count as overview evidence. The original copied-
quote regression checks are superseded by observable reference-resolution and
invalid-reference REST checks because the provider output contract changed.

The strict-schema probe for case 11 completed all three explanations. The same
unchanged nine-case follow-up file is rerun into a separate references artifact;
the first nine-case artifact with two fallbacks remains retained. Final results: **27/27 explanations completed across all nine cases**, with
no explanation fallbacks. See [FEEDBACK_RESULTS.md](FEEDBACK_RESULTS.md) for
actual final text, evidence, costs, and limitations. Temporary tagged diagnostic logging is
confined to an isolated disposable container and is removed after verification.


Final independent review identified a semantic error in the new case-14 sample:
the `(500) Days of Summer` explanation moved the 500-day relationship duration to
a post-breakup reflection period. This response is **not accepted as grounded**.
The original output remains visible; 27/27 means completion only. A concise final
prompt rule preserves chronology, quantities, durations and causal relationships,
but is not presented as proof that future claims are entailed. The original
owner's case-14 feedback concerned an earlier response and does not accept this
new erroneous sentence. No selective rerun replaces the failure.
