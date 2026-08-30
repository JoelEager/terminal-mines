# Development Notes
## AI Solver
Win rates:
| Difficulty | v2.0 | v1.5 |
| --- | --- | --- |
| balanced | 89% | 78% |
| challenging | 73% | 55% |
| max | 53% | 19% |
| easy | 75% | 52% |
| intermediate | 66% | 44% |
| expert | 19% | 2% |

Additionally, processing time for v2.0 is less than half of what it was for v1.5.

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
```
