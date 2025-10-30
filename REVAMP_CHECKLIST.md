# Revamp Checklist

This document tracks the high-level project revamp items.

| # | Item | Description | Status | Notes |
|---|------|-------------|--------|-------|
| 1 | New UI page: Tasks Manager | Build the Tasks Manager page with Completed + Next tabs, governance banner and side-task policy. | done | Implemented; notes and scrollable layman descriptions added. (Completed 2025-10-29T19:06:44.962023Z) |
| 2 | Future enhancements categorized | Produce a Must-have vs Good-to-have list for future work and store in the app. | done | Stored in tasks.json under Future enhancements. |
| 3 | Staying on track — governance rule | Agree and enforce a governance rule (sprint banner, side tasks) so we keep on the sprint and track tangents as side tasks. | done | `side` flag and sprint policy implemented in Tasks Manager. |
| 4 | App Work Flow, scaled execution plan | Define the scaled process for dev vs prod (job-runner, async workers, artifacts, job lifecycle). | todo | Phase B (job runner) is planned next. |
| 5 | Replan UI + reorganize JSON/data files | Consolidate generated artifacts under `/data` and logs under `/logs`, and reorganize tools outputs into these folders. | todo | Will add tools/organize_data.sh and update UI to point to /data and /logs. |
| 6 | Clean up note | Scan repo for unused scripts and produce `cleanup_candidates.json` for review and removal/archival. | todo | This will be a manual review step; candidate file to be generated. |