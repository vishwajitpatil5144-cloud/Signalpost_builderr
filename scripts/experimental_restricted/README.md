# Quarantined — not part of the default signal_scrape pipeline

These scripts came with the original starter kit and touch LinkedIn directly
(guest-mode scraping / unofficial company-profile discovery). They are kept
here, untouched, only for reference.

They are **excluded from `PIPELINE.md`, `run_full_pipeline.sh`, and every
step-by-step instruction in this project** for two reasons:

1. **Source policy.** `docs/norway-sources.md` and Builderr's public
   `signalpost-sources.md` both say the same thing: an unofficial LinkedIn
   client is not made acceptable just because the code exists on GitHub, and
   any such connector must be declared and independently re-verified from a
   durable *permitted* source before anything from it is published. Treating
   its output as evidence, on its own, breaks the 95%-precision hard gate if
   it goes wrong.
2. **It isn't needed.** The free, deterministic pipeline in this project
   (registry → registry-website → free domain-guess discovery → static crawl
   → deterministic synthesis) can hit the qualification bar without ever
   touching a restricted platform.

If you want to experiment with these privately, that's allowed under the
playbook ("may be evaluated in a private experiment"), but do not wire their
output into `out/envelopes.jsonl` as a source of truth, and do not submit an
entry that depends on them.
