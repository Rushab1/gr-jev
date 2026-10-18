# Open items in the abstract and introduction, 2026-10-15

Found by Claude Code when aligning the setup section with the abstract and the introduction. The abstract and the
introduction were not edited. Rushab asked to note them here.

1. A claim with no matching measure. `paper/sections/introduction.tex:26` says "We also compare the gap with that
   from an alternative formulation that asks one yes/no question per choice." Neither the setup nor the results
   compute a gap for the yes/no questions. Either drop "the gap" from that sentence or add the measure.
2. A number not checked. The abstract (`paper/sections/abstract.tex:1`) and the introduction
   (`paper/sections/introduction.tex:32`) give calibration gaps of up to 27 percentage points. It has not been
   checked against the bins of the yes/no answers in `docs/paper_runs.html`, finding 4.
3. Small fixes:
   - "abel" should be "able" in `paper/sections/introduction.tex:28`.
   - The introduction uses " - " as a dash at lines 17 and 28.
   - The abstract has two em dashes, around "Jev, Liquid d1, and GPT-6 Luna Decisions".
