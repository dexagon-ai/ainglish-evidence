# Retracted predecessor

Attempt `98f70b11-f825-47c5-8749-6eed2cf1cb33` and manifest
`974da1a9a41327db9ff460917291f0e6af1bb3a7fae433e02fe0baf1126d63a0`
were retracted by Dexagon at `2026-08-31T09:44:54Z`.

The isolated test worktree inherited Composer metadata generated in another
worktree, so `App\Kernel` could not autoload. All six tests errored before any
assertion. The manifest required the tests to execute, but the first runner
incorrectly converted that harness failure into `unclaimed_verdict_flips = 1`.
No implementation verdict flip had been observed.

The public retraction reason is carried by the Ainglish measurement record. The
corrected standalone original is attempt `295a2616-8c0c-4ca6-b922-6bef1892ad24`,
manifest `ce447a4baed59817ccfc059d43b416b2caa96e2bfa1ee815378bacfd5186a23c`.
Its manifest names the predecessor as `supersedes_attempt_id`, but it is not
presented as a server-linked correction: the server correctly refused that link
because the corrected manifest did not use the required `correction_of` field.
