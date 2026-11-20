# Design

## Workflow

```mermaid
flowchart LR
  L[Govt list of records with a dead owner] --> U[Village accountant / CSC reaches the family]
  U --> V[Kannada voice + RTC photo]
  V --> A[Agent]
  A --> T1[Read RTC: Sarvam Vision]
  A --> T2[Heir rules engine]
  A --> T3[Live record check: pending mutations, revenue cases]
  A --> T4[Map risks: lake, drain, encroachment, power line]
  T1 --> A
  T2 --> A
  T3 --> A
  T4 --> A
  A --> C[Daughter's own consent if she gives up her share]
  C --> O[Checklist + filled Pauti Khate application, WhatsApp or print]
```

0. **Reach out:** Karnataka found about 45 lakh land parcels linked to dead owners through Aadhaar seeding ([South First](https://thesouthfirst.com/karnataka/what-are-karnatakas-land-beat-and-aadhaar-seeding-initiatives-that-aim-to-transform-land-management)). Starting from that list, the village accountant or service centre contacts each family. Japan and Rwanda show that waiting for heirs to come forward leaves records stale. Whether the list can be shared with operators is something to confirm with the Revenue Department.
1. **Talk:** survey number, who died, who is alive (spouse, sons, daughters, children of a child who died), any partition or will. One question at a time.
2. **Read:** Sarvam Vision reads owners, extent and survey number from the RTC photo. These are cross-checked against cadastral data; anything that doesn't match is asked back.
3. **Heirs:** a rules engine applies the Hindu Succession Act (as amended in 2005, daughters equal), other personal laws as separate rule sets. Output: each heir and share, explained in Kannada.
4. **Blockers:** pending mutations and revenue cases for the survey number, plus map overlaps. Each one comes with the office to visit and what to bring.
4b. **Consent:** if a daughter gives up her share, she confirms it herself, in a separate call or visit, not through the family. Research shows families have worked around equal inheritance by moving land to sons (Roy 2015).
5. **Two steps if needed:** the family can record the heirs first and settle division later, where Karnataka's process allows. Japan's heir declaration works this way.
6. **Hand over:** checklist and pre-filled application, sent on WhatsApp or printed at the service centre.

Unusual cases (a will, a dispute, a court case) are flagged and sent to the revenue office. The agent never guesses them.

## Stack

| Layer | Pieces |
|---|---|
| Channels | WhatsApp bot, service centre operator web app, printable PDF |
| Language | IndicConformer (Kannada speech to text), Jugalbandi-style voice flow, Sarvam Vision (RTC only) |
| Agent | LLM with tool calling, case file (who died, heirs, documents, next step) |
| Tools | heir rules engine (Python, tested), record checks, map overlays, form filler |
| Data | Karnataka cadastral maps, overlay layers from public maps |

## Business model

Free for families. Banks, NBFCs and cooperatives pay per land report before a loan; service centres pay per completed application.
