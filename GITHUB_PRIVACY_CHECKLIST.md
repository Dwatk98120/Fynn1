# GitHub Privacy Checklist

Before pushing the project:

- [ ] No child/student audio files are included.
- [ ] No student names, IDs, photos, or notes are included.
- [ ] No exported student reports are included.
- [ ] No API keys or passwords are included.
- [ ] No signing keystore is included.
- [ ] `.gitignore` is committed.
- [ ] Repository visibility is appropriate for the project.
- [ ] Speech-analysis API uses HTTPS.
- [ ] GitHub variables/secrets contain only necessary configuration.
- [ ] Production releases are signed separately from debug builds.

If a secret is accidentally committed, rotate/revoke it; deleting the file in a later commit does not make the original secret safe.
