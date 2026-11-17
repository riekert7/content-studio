# Critic rubric

The critic scores each option 1 to 5 on six criteria. The exact text it receives is in `agents/critic.md`; keep the two identical.

<!-- rubric:start -->
Score every option 1 to 5 on each of six criteria. 5 is excellent, 3 is mediocre, 1 is broken.

- evidence: the hook rests on something real and checkable, not on a claim with nothing behind it.
- value: a viewer gets something (a fact, a laugh, a feeling) in the first 10 seconds.
- send_reason: you can name who would send this to whom, and why.
- hook: the first 1.5 seconds put a person and a stake on screen, with no greeting and no logo.
- originality: it does not look like the same video everyone already makes.
- rules: it makes no claim a business could not defend, and does not pitch before it earns attention.

Any score below 4 must carry a quote: words copied exactly from the packet that show the problem. A score below 4 with no exact quote counts as 4.
<!-- rubric:end -->

## What the code does with the marks

`cs verify` rejects any score below 4 whose quote is not an exact piece of the packet (whitespace ignored) and counts it as 4. An option is dropped under 18 of 30 or with any score of 1. The out-there option is never dropped on score alone: it is flagged "below threshold, your call".
