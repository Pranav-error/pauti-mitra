# Pauti Mitra

A Kannada voice agent that helps families transfer inherited land records.

Tech4Bharat (GAVS 2026), Theme 1: Real Estate and Land, problem 1.2: land records too unclear to sell, inherit or borrow against.

## The problem in one line

About 48 lakh land records (RTCs) in Karnataka still list an owner who has died. Until the record moves to the heirs, the family can't sell the land, divide it, get a loan against it or claim schemes tied to land.

## What Pauti Mitra does

1. The family (or a village accountant / service centre operator) talks to it in Kannada.
2. It reads a photo of the RTC.
3. It works out the legal heirs and their shares with fixed, tested rules (daughters included).
4. It checks the survey number for anything that will block the transfer: pending mutations, pending revenue cases, lake / drain / encroachment overlap.
5. It hands back a document checklist and a filled Pauti Khate application, on WhatsApp or printed.

The LLM asks and explains. Who inherits, and what blocks the transfer, is decided by code and live data.

## Repo

| Folder | What's inside |
|---|---|
| [docs/problem.md](docs/problem.md) | The problem, with numbers and sources |
| [docs/research.md](docs/research.md) | Papers and reports we used |
| [docs/existing-tech.md](docs/existing-tech.md) | What already exists (Landeed, the government campaign, open models) and what we reuse |
| [docs/design.md](docs/design.md) | Workflow and stack |
| [docs/gaps-and-plan.md](docs/gaps-and-plan.md) | Open gaps, how we close them, build plan, risks |
| [deck/](deck/) | Idea submission deck (PDF + HTML source) |

## Status

Idea stage. Everything described here is planned work for the prototype phase.
