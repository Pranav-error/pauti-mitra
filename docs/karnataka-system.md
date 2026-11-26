# How inheritance transfer works in Karnataka (and where we plug in)

Researched 2026-11-27. The main source is the IIHS *Evaluation of Quality of Land Records, Karnataka* (draft, written for the Department of Land Resources, 2025, [PDF][iihs]). Other sources are linked inline. Where sources disagree, both versions are given.

## The pieces

| System | What it is | Who runs it |
|---|---|---|
| **RTC / Pahani** | Record of Rights, Tenancy and Crops. One per survey number and hissa (sub-number). Village Account Form No. 2 | Revenue Dept |
| **Bhoomi** | Holds every rural RTC and the mutation register; landrecords.karnataka.gov.in | Bhoomi Monitoring Cell |
| **Mutation (MR)** | *Any* change to an RTC is a mutation, with an MR number. Inheritance is one type: **ಪೌತಿ (pouthi)** | Revenue Inspector approves |
| **e-Pouthi** | Revenue Dept software and drive to move dead owners' land to heirs ([South First, Feb 2026][sf26]) | Village officer (VAO/GAO) |
| **Nadakacheri** | Hobli-level citizen service centre. Files unregistered mutations; issues the family tree certificate | Deputy Tahsildar |
| **e-Chawadi** | Public view of mutations, revenue court (RCCMS) cases, e-Pouthi pending / ongoing / disposed | Revenue Dept |
| **RCCMS** | Revenue court case system. Disputed mutations end up here | Tahsildar / AC / DC |
| **KAVERI 2.0** | Registration of sale, gift and partition deeds. Sends a **J-slip** to Bhoomi, which starts a mutation automatically | Registration Dept |
| **Mojini / 11E / podi** | Survey sketches. Podi (phodi) splits a survey number into hissas after a division | Survey Dept |

## The RTC, column by column (IIHS p.9, checked against the sample in IIHS Annexure 1)

| Col | Holds | Why we read it |
|---|---|---|
| 1, 2 | Survey number, hissa | the lookup key |
| 3 | Extent (acre.gunta.anna.paisa; 40 guntas = 1 acre), kharab | shares are worked out on this |
| 4 | Land revenue assessment | |
| 5, 6, 7, 8 | Soil, patta (often ಸರ್ಕಾರಿ), trees, irrigation | |
| **9** | **Owners**: name with father's name, extent held, khata no. | who is on the record; dead owners show up here |
| **10** | **How each owner got it**: MR number, date, type (ಪೌತಿ inheritance, ಕ್ರಯ sale, ...) | history; an earlier ಪೌತಿ shows inheritance has happened before |
| **11** | Other rights (ಹಕ್ಕುಗಳು) and liabilities (ಋಣಗಳು): loans, mortgages, court stays | loans pass to the heirs; stays block the transfer |
| 12, 13 | Cultivator per season, crops | a cultivator who isn't the owner may mean tenancy |

**Reading tips from the real sample:** "ಬಿನ್ ಲೇ" (bin le) means *son of the late* ..., so the word ಲೇ marks a dead parent. Names with 0.00 extent can be leftover errors (IIHS p.16). "ಮೂಲಖಾತೆದಾರರು" means the original khata holders. Column numbering differs between guides, so read by the printed headings.

## How a pouthi (inheritance) mutation runs

1. **Trigger.** Either the heirs apply at the Nadakacheri, or the village officer finds them through the e-Pouthi drive. Since Aadhaar seeding, the state knows which RTCs have a dead owner: village officers reported **about 48 lakh** ([IIHS p.16][iihs]). A Feb 2026 report says **45 lakh parcels**, with **14,48,536 survey numbers cleared** through e-Pouthi so far ([South First][sf26]).
2. **Prove who the heirs are.** The commonly cited documents are:
   - the **death certificate**;
   - a **family tree certificate (ವಂಶವೃಕ್ಷ)**, from the Nadakacheri / Seva Sindhu. The Sakala timeline is 14 days. It needs an affidavit and a hand-drawn family tree ([ClearTax][fam]; fee and stamp-paper amounts differ between sources);
   - the current RTC;
   - Aadhaar for each heir.
3. **Aadhaar eKYC by OTP.** The village officer's app sends OTPs. The government gives an OTP, then eKYC runs with an OTP from the Aadhaar server, then a final government OTP. The owner or heir reads these out to the officer ([South First, Aug 2024][sf24]). **So every heir's Aadhaar must be linked to a mobile number that works.**
4. **Mutation entry.** At the Nadakacheri, a data-entry operator enters it, the shirastedar verifies it and gives an **MR number**, and the Revenue Inspector acknowledges it ([IIHS p.28-29][iihs]).
5. **Notice or auto-mutation.** The IIHS report says two different things here:
   - **Box 3, "with notice":** an unregistered inheritance or partition mutation gets a **15-day notice**. The Sakala timeline is **40 days**; the average in 2024 was 17.5 days.
   - **Box 3, "without notice":** **pouthi khatha** is in the auto-mutation list. The Sakala timeline is **5 days**; the average is 0.73 days. Auto-mutation started in April 2024.
   - Our reading: an uncontested e-Pouthi case goes through auto-mutation, and anything with a notice or objection takes the 15-day path. **To confirm with a Nadakacheri.**
6. **Objection.** There's no online objection. Someone objecting has to go to the taluk office or Nadakacheri. The objection becomes an **RCCMS case**, which the Tahsildar decides within 45 days for unregistered mutations ([IIHS p.28][iihs]). This is the "pending revenue court case" our blocker check reads.
7. **Done.** The RI approves, Bhoomi issues a digitally signed RTC, and **every heir is entered in column 9 as a joint owner.**
8. **Division (separate, optional, later).** Splitting the land between the heirs is a different track: a partition (registered deed or family arrangement), an 11E pre-mutation sketch, then **podi** into hissas, each with its own RTC (commercial land-service guides; the exact order is not confirmed from an official source). The IIHS village survey found 53% of parcels had several owners who **never apply for a partition**. They share the land informally (p.4).

**Law behind it:** Karnataka Land Revenue Act s.128 says whoever acquires a right must report it within 3 months, and late reports are accepted with a small penalty. The rules require the mutation register entries to be displayed in the chavadi for 30 days (as quoted in Karnataka High Court judgments; statute text not yet checked). Succession itself follows personal law; for Hindus that's what `engine/heirs.py` handles.

## Where families get stuck (what we fix)

| Stuck point | Evidence | Pauti Mitra |
|---|---|---|
| They never apply | 11% of parcels didn't match the ground, mainly because the inheritance was never updated. Officers say families "do not feel the necessity" (IIHS p.41) | outreach from the dead-owner list; explain what they lose (loans, sale, schemes) |
| They don't know who counts as an heir | daughters left out ([Deccan Herald][dh]) | `heirs.py` names every Class I heir, daughters included |
| Family tree certificate | needs an affidavit and a drawn tree; fees vary | **we draft the family tree and affidavit from the conversation**, listing every daughter |
| Aadhaar OTP on the day of the visit | 3 OTPs per heir; a heir far away or with no linked mobile stalls it | checklist: each heir's Aadhaar linked to a mobile, available on the visit day |
| Hidden blockers | pending RCCMS case, a mutation already in progress, an e-Pouthi already filed | `blockers.py` checks e-Chawadi live |
| Disputes | objection means RCCMS, 45 days | flag it early; heirs first, division later |
| Thinking division must come first | the state's own flow puts heirs in jointly first; podi is separate | say so plainly: you don't have to agree on the split to get onto the RTC |
| Many visits | 23% of applicants visited the office more than once (IIHS p.41) | one checklist, every document ready before the visit |

## Bhoomi "View RTC" (public, tested 2026-11-27)

landrecords.karnataka.gov.in/service2/RTC.aspx has no login and no captcha. You pick district, taluk, hobli, village and survey number, then surnoc, hissa, period and year. It returns two things:
- **an owner table:** name, extent, category, government restriction, court stay, alienated, plus "ongoing mutation" and "PYKI" flags;
- **the rendered RTC** as a PNG.

The district, taluk, hobli and village codes are the same ones e-Chawadi uses.

**What we saw when we tested Sarvam on real RTCs:**
- **The clean IIHS sample read well:** owner, extent, khata and the ಪೌತಿ MR in column 10.
- **A live Bhoomi rendering lost the column 9 owner.** Long names overflow into the extent column (Doddamaskal 16/*/2), and the name only came back from the cultivator column, misspelled.
- **The portal's own owner table also differs from the printed RTC:** it drops "ಬಿನ್", and writes the extent as "1.5.0" (acre.gunta.anna) where the RTC prints "1.05.00.00".

## Reading RTC photos: Tesseract vs Sarvam (40 real Bhoomi RTCs, 8 districts, 2026-11-27)

The raw text from each engine was scored against the portal's own owner table (`tools/compare_ocr.py`):

| | Village | Survey no. | Owner names | Cost | Time |
|---|---|---|---|---|---|
| Tesseract kan+eng (local) | 90% | **100%** | 46% | Rs 0 | ~4 s |
| Sarvam document intelligence | **97.5%** | 62.5% | **85%** | ~Rs 0.5 | ~5.6 s |

**They're good at different things.** Tesseract reads numbers reliably; Sarvam reads Kannada names much better. So we chain them, in the InfrX pattern: each step runs only when the cheaper one before it fails.
- Tesseract and rules find the record (`engine/rtc_reader.py`): **80% exact match, 90% in the top 5**.
- Sarvam's village reading is added only when that fails (8 of 40 RTCs): **82.5% exact, 90% in the top 5**.
- The rest are villages that share a name, or survey numbers Tesseract didn't read. There we ask the family one question ("which taluk?") instead of running more OCR.
- Owners always come from Bhoomi, so Sarvam's better name reading matters less.

## What this changes in our design

1. **"Heirs first, division later" isn't something we have to argue for.** It's already how Karnataka works: pouthi puts every heir on the RTC jointly, and podi or partition is a separate, optional step. We stop calling it a Japanese idea and point to the state's own process.
2. **Our biggest new output is the family tree certificate pack:** the drawn family tree, an affidavit draft, and each heir's document list. That's the one paper the family has to produce themselves.
3. **We prepare for the Aadhaar OTP day:** all heirs reachable, mobiles linked, daughters' consent already taken separately.
4. **The photo is used to find the record; Bhoomi supplies the facts.** From the RTC photo we take the village, survey number and hissa. The owners come from Bhoomi's own owner table, not from reading the image. Reading the image is only a cross-check, and is used for columns 10 and 11 (earlier ಪೌತಿ, loans, stays). This is because reading names off real RTCs is unreliable (see above). For production, ask the Revenue Department for proper API access instead of filling in the public form automatically.
5. **We track the case afterwards:** the MR number on e-Chawadi (mutation status, RCCMS, e-Pouthi), which `blockers.py` already reads.

## Still to confirm on the ground
- [ ] Uncontested pouthi: auto-mutation (5 days) or a 15-day notice? (The IIHS report says both.)
- [ ] The current Nadakacheri fee and stamp paper for the family tree certificate.
- [ ] Can heirs living outside Karnataka now apply? (One 2026 report says yes ([moggs][nri]); not confirmed.)
- [ ] Does the e-Pouthi app take requests started by heirs, or only by the village officer?

[iihs]: https://cdnbbsr.s3waas.gov.in/s3d69116f8b0140cdeb1f99a4d5096ffe4/uploads/2025/07/20250730596089689.pdf
[sf26]: https://thesouthfirst.com/karnataka/bhoo-guarantee-karnatakas-push-to-clean-up-land-records-grant-ownership/
[sf24]: https://thesouthfirst.com/karnataka/what-are-karnatakas-land-beat-and-aadhaar-seeding-initiatives-that-aim-to-transform-land-management
[fam]: https://cleartax.in/s/family-tree-certificate-karnataka
[dh]: https://www.deccanherald.com/india/karnataka/kin-denying-women-land-share-karnataka-minister-krishna-byre-gowda-3895511
[nri]: https://moggs.in/news/karnataka-farmland-inheritance-rules-non-resident-heirs/
