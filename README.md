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

## Research references

Each reference below backs a specific design choice. Full notes in [docs/research.md](docs/research.md).

### Problem and scale

| # | Reference | Finding | How it shapes Pauti Mitra |
|---|---|---|---|
| 1 | Karnataka Revenue Department figures, via [Deccan Herald](https://www.deccanherald.com/india/karnataka/karnataka-has-29-lakh-lands-in-the-name-of-dead-people-3244098) and [Hans India](https://www.thehansindia.com/karnataka/govt-launches-special-campaign-to-transfer-land-records-to-heirs-942796) | About 45 to 52 lakh RTCs still in deceased owners' names; families don't apply because of fees, disputes, unclear heirs, missing documents | Target the inheritance mutation (pauti) and the reasons families stall |
| 2 | [PRS Legislative Research, Land Records and Titles in India](https://prsindia.org/policy/analytical-reports/land-records-and-titles-india) | 86% of land records computerised but only 47% of mutations | The gap is in updating records, not storing them |
| 3 | [Lok Sabha Standing Committee on Rural Development, Report 41 (2026)](https://sansad.in/getFile/app/lsscommittee/Rural%20Development%20and%20Panchayati%20Raj/18_Rural_Development_and_Panchayati_Raj_41.pdf?source=app) | Inheritance, partition and court-order changes not reflected promptly | Confirms inheritance as a priority case |
| 4 | [Damle and Gulati, land litigation study, Delhi High Court (Carnegie India, 2021)](https://carnegieendowment.org/events/2021/09/land-litigation-in-india-learnings-from-a-study-on-land-litigation-in-delhi) | Record-related disputes are 13.6% of property litigation there | We don't claim to fix court backlogs; we fix one process |
| 5 | [Deccan Herald, Revenue Minister on women's land share](https://www.deccanherald.com/india/karnataka/kin-denying-women-land-share-karnataka-minister-krishna-byre-gowda-3895511) | Relatives deny women their share | Heir shares computed by rules and shown openly, daughters included |

### Why clear title matters

| # | Reference | Finding | How it shapes Pauti Mitra |
|---|---|---|---|
| 6 | [Prabhakar, Sanan, Sen, NCAER working paper: land as collateral](https://ncaer.org/?p=14819) | Clear title favours institutional loans | Lender land report as the business model |
| 7 | [Chakraborty et al., land as collateral in India](https://judhajitc.github.io/files/LandascollateralinIndia.pdf) | Cheap information on ownership and encumbrances lets lenders judge collateral | Blocker check doubles as a lender report |
| 8 | [EAC-PM, Unlocking property rights through SVAMITVA (2026)](https://eacpm.gov.in/wp-content/uploads/2026/04/Unlocking-property-rights-through-SVAMITVA-Fin-rev.pdf) | Formal property rights helped women and lower-income groups get collateral credit | Impact case for rural and women heirs |
| 9 | [AERC Study 194, Visva-Bharati (2026)](https://www.visvabharati.ac.in/home/wp-content/uploads/2026/02/AERC_Study-194_02.pdf) | Clear titles raise investment and access to institutional credit | Impact case |
| 10 | [ISEC Policy Brief 59 (2025)](https://www.isec.ac.in/wp-content/uploads/2025/06/PB-59-Strengthening-Land-Titling-to-Enhance-Farmers-Final.pdf) | Unclear titles mean fewer government scheme benefits | Impact case |

### Technology for low-literacy users

| # | Reference | Finding | How it shapes Pauti Mitra |
|---|---|---|---|
| 11 | [Nyay Sahayak, ITM Web of Conferences (2026)](https://www.itm-conferences.org/articles/itmconf/pdf/2026/01/itmconf_etmis2025_01003.pdf) | Voice-first legal aid in 22 languages for low-literacy users; not built for land | Voice-first design; land is the open gap |
| 12 | [Large Language Models Humanize Technology, arXiv 2305.05576 (2023)](https://arxiv.org/pdf/2305.05576) | LLM voice bots can serve farmers in their language, but accuracy drops for low-resource languages | Keep legal decisions in rules, not the LLM |
| 13 | [AI4Bharat IndicConformer](https://github.com/AI4Bharat/IndicConformerASR) | Open Kannada speech recognition (MIT) | Kannada speech to text |
| 14 | [Jugalbandi, AI4Bharat, OpenNyAI and Microsoft](https://www.thoughtworks.com/en-ca/clients/jugalbandi) | WhatsApp voice pipeline for government schemes | WhatsApp voice flow |
| 15 | [Designing Production-Scale OCR for India, arXiv 2602.16430 (2026)](https://arxiv.org/html/2602.16430) and [Sarvam Vision](https://docs.sarvam.ai/api/models/sarvam-vision) | Multilingual Indian document OCR, Kannada supported | Reading the RTC photo |

### Future: land valuation

| # | Reference | Finding | How it shapes Pauti Mitra |
|---|---|---|---|
| 16 | [IIMA and SFarmsIndia, ISALPI farmland price index (2024)](https://www.iima.ac.in/sites/default/files/2024-12/ISALPI%20December%202024%20Release.pdf) | Hedonic model; distance to cities and airports drives value | Valuation shown as a range |
| 17 | [Thailand asset value from imagery, arXiv 2307.08650 (2023)](https://arxiv.org/pdf/2307.08650) and [India agricultural land segmentation, arXiv 2411.05359 (2024)](https://arxiv.org/html/2411.05359v1) | Satellite imagery plus tabular data for land value and land use | Later valuation module |

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
