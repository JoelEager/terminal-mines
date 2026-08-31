# Development Notes
## AI Solver
Win rates:
| Difficulty | Optimal play | v2.1 | v2.0 | v1.5 |
| --- | --- | --- | --- | --- |
| balanced | - | 87% | 87% | 78% |
| challenging | - | 75% | 73% | 55% |
| max | - | 55% | 52% | 19% |
| beginner | ~94% | 88% | 86% | 77% |
| intermediate | ~80% | 70% | 69% | 42% |
| expert | ~46% | 25% | 18% | 1% |

(Measured over at least 3,000 iterations targeting a precision of +/- ~1%.) Additionally, per-move processing time for v2.0 and v2.1 is less than half of what it was for v1.5.

### Tooling Usage
Run the solver in debug mode:
```sh
MINES_AI_DEBUG=step mines challenging --solve
MINES_AI_DEBUG=y mines expert --solve
```

Run the solver harness:
```sh
python solver_harness.py expert
python solver_harness.py 175,30,30 -i 100
for d in balanced challenging max beginner intermediate expert; do echo === $d ===; python solver_harness.py $d -i 3000; done
```
