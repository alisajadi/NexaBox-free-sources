# Publication acceptance — 2026-10-07

The public feed is deployed. The first [GitHub Actions run](https://github.com/alisajadi/NexaBox-free-sources/actions/runs/37610750282)
completed successfully, including all three Python unit tests, public-channel
retrieval and publishing the generated data. Its snapshot commit is
`6519472`.

The fixed endpoint returned HTTP 200 with three HTTPS references, including
the generated `channels/LonUp_M.txt`. The channel snapshot contained 167
extracted public share links. No client-provided GitHub token is required.

At `2026-10-07T10:58:33Z`, the actual NexaBox 0.7 catalog code fetched this
endpoint and its references. The acceptance fetcher refused all direct
`t.me` requests. Results:

| Check | Result |
| --- | --- |
| Direct Telegram requests attempted | 0 |
| Channel links accepted by the supported-profile parser | 117 |
| Channel links rejected by that parser | 50 |
| Unique candidates across all three references | 4038 |
| Source fetch errors | 0 |
| Managed sources hidden from ordinary source lists | Yes |

These are retrieval/import results, not proxy health or speed measurements.
Public contents and counts change; NexaBox checks actual connectivity
separately. The client still needs access to GitHub. Existing NexaBox
`0.7.0-preview` already contains the fixed URL and needs no binary update
for this deployment.

The deployed workflow refreshes on changes to `sources.txt`, on manual
dispatch and every 30 minutes, subject to GitHub scheduling limits. Edit
`sources.txt`; generated index/snapshot files are maintained by the workflow.
