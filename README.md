# TFG Solver

## Project Structure

- `data`: contains data files, like course definitions, general settings, rooms, etc.
- `src`: contains the actual logic of the solver
- `tests`: missing test cases

### Solver Logic

- `adapter`: some useful sub-packages, like the data reader
- `models`: class files, like Room, Course, Schedule, etc.
- `solvers`: all available solvers
  - `asp.constants`: Clingo constants and naming used
  - `asp.rules`: Clingo rules generator
  - `asp.scheduler`: actual solver
- `utils`: some utility code
