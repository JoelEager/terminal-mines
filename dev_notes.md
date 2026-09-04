# Development Notes
Run tests: `python -m unittest discover tests`

Check package description extraction: `python setup.py --long-description`

## AI Solver
Win rates:
| Difficulty | Optimal play | exact-prob-solver | v2.1 | v2.0 | v1.5 |
| --- | --- | --- | --- | --- | --- |
| balanced | 90% | ~90% | 90% | 87% | 78% |
| challenging | 80% | ~82% | 80% | 73% | 55% |
| max | 65% | ~60% | 60% | 52% | 19% |
| beginner | 92% | ~92% | 91% | 86% | 77% |
| intermediate | 78% | ~78% | 74% | 69% | 42% |
| expert | 40% | ~40% | 28% | 18% | 1% |

(Measured over at least 3,000 iterations targeting a precision of +/- ~1%. Optimal play win rates from minesweeper.online.)

Strategies implemented:
- **v2.1**: Simple deduction, two cell overlap flag, two cell subset reveal, low risk guess, corner guess, greenfield guess, corner start
- **v2.0**: Simple deduction, two cell subset (flag and reveal), low risk guess, greenfield guess, corner start
- **v1.5**: Simple deduction, corner guess, corner start

Additionally, per-move processing time for v2.0 and v2.1 is less than half of what it was for v1.5.

### Tooling Usage
Run the solver in debug mode:
```sh
MINES_AI_DEBUG=y mines expert --solve
MINES_AI_DEBUG=step mines challenging --solve
MINES_AI_DEBUG=two_cell_flag mines expert --solve
```

Run the solver harness:
```sh
python solver_harness.py expert
python solver_harness.py 175,30,30 -i 100
for d in balanced challenging max beginner intermediate expert; do echo === $d ===; python solver_harness.py $d -i 3000; done
```
