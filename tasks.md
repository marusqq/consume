- [x] Make X articles available to consume
  - [x] Updated `parse_args()` to accept `urls` as `nargs="+"` (one or more positional arguments)
  - Updated `parse_args()` to accept `urls` as `nargs="+"` (one or more positional arguments) — this c...
  - Updated `main()` to iterate over multiple URLs, printing `=== <url> ===` headers and blank-line sepa...
  - Updated existing `test_url_stored` → `test_single_url_stored` to match new `args.urls` attribute
  - Added `test_multiple_urls_stored` test for multi-URL parsing
  - Added `TestMainMultipleUrls` class with tests for headers, partial failure exit code, and single-URL...

- [ ] (.venv) marus@makas consume % consume --mode default https://x.com/polydao/status/2036407054630269202
• An error occurred while accessing x.com.
• Privacy-related browser extensions may be causing the issue.
• Users should disable privacy extensions and retry.
• The site recommends attempting access again after disabling extensions.
• The problem is potentially solvable through extension management.
(.venv) marus@makas consume % 

