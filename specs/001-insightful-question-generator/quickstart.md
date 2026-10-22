# Checking it works

How to check that the app does what the [specification](spec.md) asks. Setting it up and running
it locally are in the [README](../../README.md). What these checks found is recorded in the test log
and in [checklists/reviews.md](checklists/reviews.md).

*Spec Kit names this file `quickstart.md`; the numbered checks below are cited by number in
[tasks.md](tasks.md).*

## Automated tests

```bash
pytest                             # the Python checks, against a fake model
node --test "tests/*.test.mjs"     # the browser modules
```

Neither calls the live model or needs an API key.

## By hand

On the live site or a local copy, at desktop size and at phone width:

1. **Seed to questions**: submit a seed. A loading state appears at once, then 3–5 questions, none of them answered. (User Story 1)
2. **Open a question**: the new questions are about that question, not the seed. (User Story 2)
3. **Go deep, come back**: open five levels down, then click “Seed” in the trail to return to the start in one click. (User Story 3)
4. **Switch branches**: open a different question at an earlier level, then go back. The first branch reappears at once, unchanged. (FR-022, FR-025)
5. **Ask again**: on a question with questions below it, the confirmation says how many will be lost. Decline, and nothing changes; accept, and a new set appears. (User Story 4)
6. **New inquiry**: with an inquiry open, start a new one. It asks first, then clears without reloading. (FR-057)
7. **Cancel**: cancel while questions are loading. Nothing changes, and the next request works. (FR-058, FR-059)
8. **Click while busy**: try to open another question while one is loading. It is ignored. (FR-054)
9. **Empty and too-long seeds**: both are refused with a message; the second names the 2,000-character limit. (FR-002, FR-003)
10. **Failure**: with the API key wrong or missing, submitting shows a plain-language failure and the page stays usable. (FR-035, FR-039)
11. **Keyboard only**: repeat checks 1–5 without a mouse. (FR-043)
12. **Reload**: reload in the middle of an inquiry. The page starts empty. (FR-042)
