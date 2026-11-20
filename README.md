# Pauti Mitra

A Kannada voice agent that helps families transfer inherited land records.

Tech4Bharat (GAVS 2026), Theme 1: Real Estate and Land, problem 1.2: land records too unclear to sell, inherit or borrow against.

## The problem in one line

About 48 lakh land records (RTCs) in Karnataka still list an owner who has died. Until the record moves to the heirs, the family can't sell the land, divide it, get a loan against it or claim schemes tied to land.

## What Pauti Mitra does

0. **It goes to the family first.** Karnataka already knows which records have a dead owner (Aadhaar seeding). The village accountant or service centre gets the survey numbers in their village, and Pauti Mitra reaches each family, instead of waiting for them to come.
1. The family (or the accountant / operator) talks to it in Kannada.
2. It reads a photo of the RTC.
3. It works out the legal heirs and their shares with fixed, tested rules (daughters included). **If a daughter gives up her share, she is asked separately, on her own.**
4. It checks the survey number for anything that will block the transfer: pending mutations, pending revenue cases, lake / drain / encroachment overlap.
5. It hands back a document checklist and a filled Pauti Khate application, on WhatsApp or printed. **The family can start even if they haven't agreed how to divide the land:** heirs are recorded first, division later, where the process allows (as in Japan).

The LLM asks and explains. Who inherits, and what blocks the transfer, is decided by code and live data.

## Key research

The references that shape the design most. Full list in [docs/research.md](docs/research.md); other countries in [docs/global-approaches.md](docs/global-approaches.md).

| Reference | Finding | What it means for us |
|---|---|---|
| Karnataka Revenue Department, via [Deccan Herald](https://www.deccanherald.com/india/karnataka/karnataka-has-29-lakh-lands-in-the-name-of-dead-people-3244098), [Hans India](https://www.thehansindia.com/karnataka/govt-launches-special-campaign-to-transfer-land-records-to-heirs-942796) | About 48 lakh RTCs still in dead owners' names; families stall on fees, disputes, unclear heirs, documents | The problem we solve |
| [PRS, Land Records and Titles in India](https://prsindia.org/policy/analytical-reports/land-records-and-titles-india) | 86% of records computerised, only 47% of mutations | The gap is updating records, not storing them |
| [Deininger, Goyal, Nagarajan, J. Human Resources (2013)](https://openknowledge.worldbank.org/server/api/core/bitstreams/9dc8882f-5fbf-5df5-9aca-78a67f413fa4/content) | Karnataka's equal-share reform raised daughters' land inheritance by 22 points, but bias remained | Daughters' shares enforced by rules |
| [Roy, J. Development Economics (2015)](https://ideas.repec.org/a/eee/deveco/v114y2015icp233-251.html) | Families worked around the reform by giving land to sons | Every share shown openly; a daughter giving up hers needs her own consent |
| [NCAER, land as collateral](https://ncaer.org/?p=14819) and [EAC-PM, SVAMITVA (2026)](https://eacpm.gov.in/wp-content/uploads/2026/04/Unlocking-property-rights-through-SVAMITVA-Fin-rev.pdf) | Clear title opens formal credit, including for women and poorer households | Impact, and lenders as paying customers |
| [Medhi, Sagar, Toyama, Text-Free UIs, ITID (2007)](https://courses.cs.washington.edu/courses/cse490c/18au/readings/medhi-2007.pdf) and [Patel et al., Avaaj Otalo, CHI (2010)](https://collablab.northwestern.edu/CollabolabDistro/nucmc/PatelEtAl-AvaajOtalo-VoiceForumForSmallFarmers-2010.pdf) | Low-literacy users prefer voice; a phone voice service worked for 51 farmers over 7 months | Voice-first, no text in the family's flow |
| [Merigoux et al., Catala, ICFP (2021)](https://arxiv.org/abs/2103.03198) | Law written as testable code, paragraph by paragraph; found a bug in an official implementation | Heir rules as tested code, not an LLM guess |
| Japan, mandatory inheritance registration (2024): [Hiroshima City](https://www.city.hiroshima.lg.jp/english/paperwork/1029827/1009917.html), [Real Estate Tokyo](https://www.realestate-tokyo.com/news/inheritance-registration-mandatory) | Unregistered inheritances left land with unknown owners larger than Kyushu; Japan now requires registration within 3 years (fine up to 100,000 yen) | Same problem, solved by law plus a simple heir filing; we make the filing easy |
| [Rwanda Land Tenure Regularization, World Bank](https://openknowledge.worldbank.org/server/api/core/bitstreams/d63797f6-e70f-54b9-8dd8-6ab36c658793/content) | 8.4 million parcels registered in 3 years, but later transfers stayed unregistered | A one-time drive isn't enough; updating must stay cheap and local |
| US heirs' property: [Union of Concerned Scientists](https://ucsusa.org/resources/lost-inheritance), [Cambridge](https://www.cambridge.org/core/product/D90A1CBE535C040CFF2A267423FE3A0F) | Unresolved inheritance is a leading cause of Black farmland loss; 21 states adopted a law to protect heirs | Unclear heirs cost land; settle them early |

## Repo

| Folder | What's inside |
|---|---|
| [docs/problem.md](docs/problem.md) | The problem, with numbers and sources |
| [docs/research.md](docs/research.md) | Papers and reports we used |
| [docs/global-approaches.md](docs/global-approaches.md) | How Japan, the US, China, Estonia, Rwanda and Ethiopia handle it, and the best approach combined |
| [docs/existing-tech.md](docs/existing-tech.md) | What already exists (Landeed, the government campaign, open models) and what we reuse |
| [docs/design.md](docs/design.md) | Workflow and stack |
| [docs/gaps-and-plan.md](docs/gaps-and-plan.md) | Open gaps, how we close them, build plan, risks |
| [deck/](deck/) | Idea submission deck (PDF + HTML source) |

## Status

Idea stage. Everything described here is planned work for the prototype phase.
