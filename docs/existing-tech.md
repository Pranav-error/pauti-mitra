# What already exists

## Services

| | Landeed | Government Pauti Khate campaign | Pauti Mitra |
|---|---|---|---|
| Cost to family | paid fee (fixed, quoted per case) | free | free |
| How it's used | WhatsApp scans, chat assistant ("Terra"), then a specialist calls | village accountants visit homes and prepare family trees | Kannada voice, or run by the village accountant / service centre |
| Who are the heirs | handled by their staff | family tree by the accountant | tested rules, shares shown, daughters included |
| Blockers checked before applying | not stated | not stated | pending mutation, revenue case, lake / drain / encroachment |
| Best for | people who can pay and upload documents | wherever staff reach | low literacy, low-cost phone, rural |

Sources: [Landeed inheritance transfer bundle](https://web.landeed.com/products/karnataka/inheritance-transfer-bundle), [Hans India](https://www.thehansindia.com/karnataka/govt-launches-special-campaign-to-transfer-land-records-to-heirs-942796), [Star of Mysore](https://starofmysore.com/district-minister-launches-e-pauti-khata-during-janata-darshan/amp).

Process facts we reuse (from Landeed's page, to be confirmed against official sources): family tree certificate in 14 working days and khata transfer in 30 working days under Sakala; agricultural land needs a 30-day notice. Form-1 for pauti is available at revenue offices.

Documents usually needed: death certificate; deed or grant in the deceased's name; latest RTC / khata and tax receipt; Aadhaar and address proof for each heir; family ration card; optional will, and a registered power of attorney for an heir who can't attend.

## Tech we reuse

| Need | What we use | Notes |
|---|---|---|
| Kannada speech to text | [AI4Bharat IndicConformer](https://github.com/AI4Bharat/IndicConformerASR) ([Hugging Face](https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual)) | Open, MIT licence |
| WhatsApp voice flow | [Jugalbandi](https://www.thoughtworks.com/en-ca/clients/jugalbandi) pattern | voice note, text, answer, spoken reply |
| Reading the RTC photo | [Sarvam Vision](https://docs.sarvam.ai/api/models/sarvam-vision) | Supports Kannada; to be tested on real RTC photos |
| Heir shares | our own rules engine | No open-source calculator found; [JuriGram](https://jurigram.com/legal-calculators/family-divorce/inheritance) only to cross-check test cases |
| Record checks and map overlays | our own (to build) | Live pending mutations and revenue cases from public e-Chawadi services; lake, drain, encroachment, power-line layers from public maps |
