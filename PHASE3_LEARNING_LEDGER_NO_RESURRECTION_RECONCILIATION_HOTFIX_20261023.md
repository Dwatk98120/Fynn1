# Hearlium Branch 2 — Phase 3 Learning Ledger + Reconciliation Hotfix

Date: 2026-10-23

## Scope

This is a full Branch 2 source ZIP for the Windows Parent PC, including the
existing Android source **without modifications**. The protected Main branch
and the existing Windows installer baseline (0.4.5) are not changed. This ZIP
is source code, not a precompiled Windows installer or APK.

## Problem corrected

Previously, when two legacy caregiver approvals referred to the same speech
observation and word segment, the second approval was hidden from the active
learning profile. Revoking the first approval accidentally caused the hidden
second approval to become ACTIVE. In Learning History, a suppressed duplicate
could also be displayed as REVOKED despite never having been revoked.

Example: caregiver revokes a learned **seven**; a historical, duplicate **eight**
must never become active simply because seven was removed.

## Changes

1. The local Parent PC learning ledger retains a stable owner for each
   observation and segment, even after that owner is revoked. Historical
   duplicate approvals cannot silently reactivate or affect future rankings.
2. Learning History distinguishes three states:
   - **ACTIVE**: influences personalized recognition rankings.
   - **REVOKED**: explicitly rolled back by a caregiver.
   - **SUPERSEDED**: inactive duplicate from older ledger history; not revoked
     and not automatically eligible to become active.
3. A fresh caregiver approval after verified rollback is allowed only as an
   explicit action; the new approval records the preceding revoked example ID.
   Its audit link survives a Parent PC restart.
4. Caregivers can revoke a SUPERSEDED duplicate explicitly or retry local
   reconciliation for an already-REVOKED example.
5. When server rollback succeeds but matching local recording metadata cannot
   safely be found, the Parent PC reports a more specific reconciliation
   diagnostic. It does not clear unrelated pending approvals or substitute a
   different request ID.
6. Original audio, acoustic observations, previous analyses, approvals,
   revocations, and their evidence hashes remain protected. No old ledger
   events are deleted or rewritten.

## Verification performed

- 141 available automated server/Parent PC `unittest` tests passed, including
  the ledger no-resurrection and rollback/reconciliation regression tests.
- One separate pytest-only test module could not be run in the supplied
  environment because `pytest` was not installed. It was not counted as passed.
- The Android source, Gradle files, and GitHub workflows were compared to the
  previous full-source ZIP baseline; their contents were unchanged.

## How to use

1. Keep a backup of the current working Branch 2 files and Parent PC data.
2. Extract this ZIP and apply its source to your Branch 2
   (`hearlium-parent-pc-integration`) workflow. Do not merge it into Main.
3. Build and install the Parent PC software using the existing Windows
   installer workflow. The installer version is intentionally unchanged.
4. Test a disposable sample: approve a word, simulate a suppressed duplicate,
   revoke the first approval, refresh Learning History, and verify that the
   duplicate stays SUPERSEDED and the approved-example count decreases.
5. If a rollback reports that local recording metadata was not reconciled,
   examine that recording's local warning and identifiers before retrying;
   never assume a successful server rollback cleared every local warning.

## Remaining validation

This package was tested at the source-code level, not installed on a Windows
machine or tested against existing real-world caregiver data. Keep the test
recordings separate from protected student evidence when verifying this build.
