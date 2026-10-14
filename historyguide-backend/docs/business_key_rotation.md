# Business API key rotation

The business key used by earlier NK-GeniOS plugins was exposed in chat and must be replaced before visitor-facing publication. This file does not contain any key value or claim that rotation has occurred.

1. Identify the **running** backend version, systemd unit or container configuration, secret source, and every caller using `X-HistoryGuide-Api-Key`. Screenshots of an old unit file are not sufficient evidence. Keep a rollback plan and note the start time.
2. Generate a fresh high-entropy secret in the deployment secret manager. Do not print it in terminals, logs, screenshots, documents, or chats. Ensure the operator key is distinct.
3. With the old key still configured as `HISTORYGUIDE_API_KEY` or `HISTORYGUIDE_API_KEY_FILE`, temporarily configure the new key as `HISTORYGUIDE_API_KEY_NEXT` or `HISTORYGUIDE_API_KEY_NEXT_FILE` and restart/reload the deployed service. Confirm missing/wrong keys return 401 and the **new** key works against a protected API. `GET /api/system/security-status` (operator-only) should report `business_api_key_rotation_staged=true` without revealing either key.
4. Update every NK-GeniOS plugin using the business key, including Handoff, legacy Review, and any new run plugin, through plugin authentication settings. Test each tool independently and an Agent end-to-end staging run. Do not put the key in the Agent prompt or an ordinary tool parameter.
5. Promote the new key to the primary direct or `_FILE` setting, remove both `HISTORYGUIDE_API_KEY_NEXT` and `HISTORYGUIDE_API_KEY_NEXT_FILE`, and restart/reload. Confirm the old key returns 401 on protected APIs while the new key still works. Check plugin runs, audit/operational alerts, and that no secret value appeared in logs.
6. Record the rotation completion time, affected service/plugin versions, and pass/fail results **without recording key values**. Do not publish the Agent until old-key rejection and all plugin tests are verified.

This repository now supports absolute-path `_FILE` settings for business, next, and operator keys. Never configure a direct key and its `_FILE` counterpart together. Before changing the running service, verify its deployed build and actual systemd/container secret mechanism; older builds may not support `_FILE`, and a screenshot does not prove the current configuration. Do not read, print, or copy the old key into chat or logs.

The dual-key period is a short migration window, not a steady-state configuration. If the old key is actively abused, prioritize revocation over uninterrupted plugin availability.
