# BPMN-to-PDDL Translator

This project translates BPMN 2.0 process models into PDDL (Planning Domain Definition Language) scripts that can be used with automated planners to simulate or reason about business processes.

##  Purpose

Business Process Model and Notation (BPMN) is a widely used standard for representing workflows. Planning Domain Definition Language (PDDL) is the standard input for many AI planners.

This project bridges the two by:
- Flattening a BPMN diagram into a logical model.
- Generating a PDDL domain file with all process actions.
- Optionally generating a PDDL problem file with the initial state and goal.

##  Features

- Parses BPMN 2.0 elements (tasks, events, gateways, flows).
- Merges parallel/converging gateways.
- Labels actions with pool/lane names.
- Handles exclusive, parallel, and event-based gateways.
- Supports start and end events.
- Supports message flows as control constraints.
- Outputs PDDL domain and predicates.
