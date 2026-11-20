# Gaps, plan and risks

## Gaps and how we close them

| Gap | How we close it | Status |
|---|---|---|
| Who are the heirs | Encode the Hindu Succession Act (2005 amendment) as rules, each with test cases; other personal laws as separate rule sets | to build |
| Reading a Kannada RTC | Sarvam Vision, then cross-check against cadastral data; mismatches asked back to the user | test first |
| Ownership history | Live services show only pending items; history comes from the RTC the family has | to build |
| Users who can't read | Voice only, one question at a time, operator mode for service centres | to build |
| Wrong advice | Wills, disputes and court cases flagged and sent to the revenue office | to build |
| Blocker check | Rule-based checks plus live lookups | working |

## Build plan

| Phase | Work | Done when |
|---|---|---|
| 1. Heirs + RTC | rules engine and tests, RTC reader, test on real RTC photos | heirs and shares come out of a photo |
| 2. Agent | tool calling over all four tools, case file, form filler | a text chat produces a filled form |
| 3. Voice + WhatsApp | Kannada speech in and out, WhatsApp bot, operator web app | the full flow works by voice |
| 4. Field test | 5 to 10 real families or one service centre, fix what confuses them, lender report | demo ready for the finale |

## Risks

| Risk | What we do |
|---|---|
| RTC photos read badly | Fall back to the user saying the survey number; look up the rest |
| Complex inheritance (ancestral property, many generations) | Handle the common case well; send complex cases to the revenue office |
| Live lookups change or are blocked | They are public services, not an official API; keep the check optional and cite the source record |
| Wrong legal output | Tests from the Act's own examples; the agent shows its reasoning |
| Privacy | Minimum data, consent before any lookup, nothing kept after the application |

## How we measure success

Applications completed per week, share accepted first time, days to an updated RTC, share of daughters correctly included.
