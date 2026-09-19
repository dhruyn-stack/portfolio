# Real-estate lead pipeline — 4 intake forms → CRM → follow-up → email segments

An importable n8n workflow that models the full lead flow a solo agent needs, wired the way a Zapier build would be
(one trigger, clean, decide, store, notify) so it can be ported step-for-step to Zapier or Make.

```
open-house sign-in ─┐
buyer questionnaire ┼─► normalise + tag ─► has email or phone? ─► CRM: find contact ─► exists? ─┬─► update + tags ─┐
seller / home value ┤            (source · lead type · stage)     │                              └─► create contact ─┼─► follow-up task (24 h) ─► email platform: matching segment
general contact ────┘                                             └─► no → log incomplete submission
```

What each step does:
- **Normalise + tag** — lower-cases the email, strips the phone, and derives `source` (Open house / Website – buyer / …),
  `lead_type` (Buyer / Seller / Unqualified) and `stage` (New) from which form was submitted. Tags come from the form, not from
  the agent's memory.
- **Has email or phone?** — a lead with neither can't be followed up; it is logged to a sheet instead of polluting the CRM.
- **Find-or-create** — a past client who fills a new form is updated and re-tagged, never duplicated.
- **Follow-up task in 24 h** — created on the contact so nothing sits unfollowed.
- **Email segment** — buyer / seller / general nurture, chosen by lead type, so the right sequence starts automatically.

Swap-ins: the two HTTP nodes carry the CRM's REST endpoints (Lofty shown; Follow Up Boss, kvCORE, HubSpot are the same shape),
and the email node targets Flodesk's subscribers API (Mailchimp / ConvertKit identical). Credentials are header-auth
placeholders; segment ids and the sheet id are marked `REPLACE_`.
