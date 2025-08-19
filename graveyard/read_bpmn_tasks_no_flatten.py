import xml.etree.ElementTree as ET
import html
import os
import re

class BPMNElement:
    def __init__(self, element_type, element_id, name, **kwargs):
        self.type = element_type
        self.id = element_id
        self.name = name
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        info = f"Type: {self.type}\n  id: {self.id}\n  name: {self.name}"
        for attr, value in self.__dict__.items():
            if attr not in ['type', 'id', 'name']:
                if isinstance(value, list):
                    info += f"\n  {attr}:"
                    for item in value:
                        info += f"\n    - {item}"
                else:
                    info += f"\n  {attr}: {value}"
        return info

class BPMNParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        self.namespaces = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
        self.elements = []
        self.id_mapping = {}

    def clean_name(self, name):
        if name:
            name = html.unescape(name)
            name = name.replace('\n', ' ').replace('\r', ' ').replace('&#10;', ' ').replace('&#xA;', ' ')
            name = ' '.join(name.split())
            return name
        return None

    def add_elements(self, tag, label, extra_keys=None):
        for elem in self.root.findall(f'.//bpmn:{tag}', self.namespaces):
            kwargs = {}
            if extra_keys:
                for key in extra_keys:
                    kwargs[key] = elem.get(key)
            self.elements.append(
                BPMNElement(
                    label,
                    elem.get('id'),
                    self.clean_name(elem.get('name')),
                    **kwargs
                )
            )

    def parse(self):
        self.elements.clear()

        self.add_elements('startEvent', 'Start Event')
        self.add_elements('endEvent', 'End Event')
        self.add_elements('userTask', 'User Task')
        self.add_elements('serviceTask', 'Service Task')
        self.add_elements('manualTask', 'Manual Task')
        self.add_elements('scriptTask', 'Script Task')
        self.add_elements('task', 'Task')

        # Intermediate Catch Events
        for event in self.root.findall('.//bpmn:intermediateCatchEvent', self.namespaces):
            event_type = 'Intermediate Catch Event'
            for child in event:
                tag = child.tag.split('}')[-1]
                if tag == 'messageEventDefinition':
                    event_type = 'Message Catch Event'
                elif tag == 'timerEventDefinition':
                    event_type = 'Timer Catch Event'
            self.elements.append(
                BPMNElement(
                    event_type,
                    event.get('id'),
                    self.clean_name(event.get('name'))
                )
            )

        self.add_elements('eventBasedGateway', 'Event-Based Gateway')
        self.add_elements('exclusiveGateway', 'Exclusive Gateway')
        self.add_elements('parallelGateway', 'Parallel Gateway')
        self.add_elements('sequenceFlow', 'Sequence Flow', ['sourceRef', 'targetRef'])

        # Message Flows
        for msg_flow in self.root.findall('.//bpmn:messageFlow', self.namespaces):
            self.elements.append(
                BPMNElement(
                    'Message Flow',
                    msg_flow.get('id'),
                    self.clean_name(msg_flow.get('name')),
                    sourceRef=msg_flow.get('sourceRef'),
                    targetRef=msg_flow.get('targetRef')
                )
            )

        # Lanes
        for lane in self.root.findall('.//bpmn:lane', self.namespaces):
            flow_node_refs = [ref.text for ref in lane.findall('bpmn:flowNodeRef', self.namespaces)]
            self.elements.append(
                BPMNElement(
                    'Lane',
                    lane.get('id'),
                    self.clean_name(lane.get('name')),
                    flowNodeRefs=flow_node_refs
                )
            )

        # Pools (Participants)
        for participant in self.root.findall('.//bpmn:participant', self.namespaces):
            self.elements.append(
                BPMNElement(
                    'Pool',
                    participant.get('id'),
                    self.clean_name(participant.get('name')),
                    processRef=participant.get('processRef')
                )
            )
        self.merge_duplicate_elements()

    def print_elements(self):
        for element in self.elements:
            print(element)
            print()

    def get_elements_by_type(self, element_type):
        return [e for e in self.elements if e.type == element_type]
    
    def merge_duplicate_elements(self):
        merged_elements = []
        seen = {}

        for e in self.elements:
            if e.type in ['Sequence Flow', 'Message Flow', 'Parallel Gateway', 'Exclusive Gateway', 'Inclusive Gateway', 'Event-Based Gateway']:
                merged_elements.append(e)
                continue

            key = (e.type, e.name)
            if key not in seen:
                seen[key] = e
                merged_elements.append(e)
            else:
                # Existing element is primary
                primary = seen[key]
                self.id_mapping[e.id] = primary.id  # duplicate maps to primary ID
                # Merge additional attributes
                for attr, value in e.__dict__.items():
                    if attr not in ['type', 'id', 'name']:
                        existing_value = getattr(primary, attr, None)
                        if existing_value is None:
                            setattr(primary, attr, value)
                        elif isinstance(existing_value, list):
                            combined = list(set(existing_value + value)) if isinstance(value, list) else existing_value
                            setattr(primary, attr, combined)

        self.elements = merged_elements

    def generate_pddl_domain(self, domain_name="bpmn-generated"):
        elements_by_id = {e.id: e for e in self.elements}
        outgoing = {}
        incoming = {}
        predicates = set()
        merged_tasks = set()
        skipped_gateways = set()

        def get_merged_id(element_id):
            return self.id_mapping.get(element_id, element_id)

        for flow in self.get_elements_by_type('Sequence Flow'):
            src = get_merged_id(flow.sourceRef)
            tgt = get_merged_id(flow.targetRef)
            outgoing.setdefault(src, []).append(tgt)
            incoming.setdefault(tgt, []).append(src)

        domain = f"(define (domain {domain_name})\n"
        domain += "  (:requirements :strips :typing)\n"
        domain += "  (:types task event gateway)\n\n"

        # Predicates
        domain += "  (:predicates\n"
        for e in self.elements:
            if "Event" in e.type or "Gateway" in e.type:
                domain += f"    ({e.id})\n"
                predicates.add(e.id)
            if e.type == "Exclusive Gateway":
                for flow in self.get_elements_by_type("Sequence Flow"):
                    if flow.sourceRef == e.id:
                        domain += f"    ({flow.targetRef})\n"
                        predicates.add(flow.targetRef)
        domain += "    (done)\n"
        predicates.add("done")
        domain += "  )\n\n"

        # Helper: find preconditions
        def get_immediate_preconditions(element_id):
            preconditions = set()
            for src_id in incoming.get(element_id, []):
                src_elem = elements_by_id.get(src_id)
                if src_elem:
                    if src_elem.type == "Exclusive Gateway":
                        preconditions.add(f"({element_id})")
                    elif "Event" in src_elem.type or "Gateway" in src_elem.type:
                        preconditions.add(f"({src_id})")
            if not preconditions:
                start_events = self.get_elements_by_type('StartEvent')
                if start_events:
                    preconditions.add(f"({start_events[0].id})")
            return preconditions
        
        def sanitize_name(name):
            # Replace all non-alphanumeric or underscore characters with underscore
            return re.sub(r'[^a-zA-Z0-9_]', '_', name)

        # Handle merged parallel gateway branches
        for e in self.elements:
            if e.id in merged_tasks:
                continue

            if "Parallel Gateway" in e.type:
                targets = outgoing.get(e.id, [])
                if len(targets) > 1:
                    # Trace each branch until they converge
                    paths = []
                    converging = None
                    for t in targets:
                        path = []
                        curr = t
                        while True:
                            path.append(curr)
                            nexts = outgoing.get(curr, [])
                            if len(incoming.get(curr, [])) > 1 and len(nexts) == 1:
                                converging = curr
                                break
                            if not nexts:
                                converging = None
                                break
                            curr = nexts[0]
                        paths.append(path)

                    if not paths or any(p[-1] != paths[0][-1] for p in paths):
                        continue  # not all paths converge at same element

                    converging_gateway = paths[0][-1]
                    post_converging = outgoing.get(converging_gateway, [])
                    if len(post_converging) != 1:
                        continue  # must have a single path after converging

                    after = post_converging[0]
                    skipped_gateways.update({e.id, converging_gateway})

                    # Merge all tasks in all paths
                    merged_ids = set()
                    for path in paths:
                        merged_ids.update(path[:-1])  # exclude converging gateway
                    merged_tasks.update(merged_ids)

                    # Generate merged action
                    merged_name = "__".join(
                        elements_by_id[mid].name.replace(" ", "_") if elements_by_id[mid].name else mid
                        for mid in merged_ids if mid in elements_by_id
                    )
                    preconditions = get_immediate_preconditions(e.id)
                    preconditions.add(f"({e.id})")

                    domain += f"  (:action {merged_name}\n"
                    domain += f"    :precondition (and {' '.join(sorted(preconditions))})\n"
                    domain += f"    :effect (and ({after})"
                    for pre in sorted(preconditions):
                        domain += f" (not {pre})"
                    domain += ")\n"
                    domain += "  )\n\n"

        # Generate remaining actions
        for e in self.elements:
            if e.id in merged_tasks or e.id in skipped_gateways:
                continue  # skip merged or skipped converging gateways

            if "Task" in e.type or "Gateway" in e.type:
                preconditions = get_immediate_preconditions(e.id)
                if "Gateway" in e.type:
                    preconditions.add(f"({e.id})")

                outgoing_targets = outgoing.get(e.id, [])

                effects = []
                oneof_effects = []

                if len(outgoing_targets) == 1:
                    effects = [f"({outgoing_targets[0]})"]

                elif len(outgoing_targets) > 1:
                    for target_id in outgoing_targets:
                        branch_effects = [f"({target_id})"]
                        target_elem = elements_by_id.get(target_id)
                        if target_elem and "Event" in target_elem.type:
                            for next_id in outgoing.get(target_id, []):
                                next_elem = elements_by_id.get(next_id)
                                if next_elem and "Gateway" in next_elem.type:
                                    branch_effects.append(f"({next_id})")
                        if len(branch_effects) == 1:
                            oneof_effects.append(branch_effects[0])
                        else:
                            oneof_effects.append(f"(and {' '.join(branch_effects)})")

                action_name = sanitize_name(e.name.replace(" ", "_")) if e.name else e.id
                domain += f"  (:action {action_name}\n"
                domain += f"    :precondition (and {' '.join(sorted(preconditions))})\n"
                domain += f"    :effect (and"
                if effects:
                    domain += f" {' '.join(sorted(effects))}"
                if oneof_effects:
                    domain += f" (oneof {' '.join(oneof_effects)})"
                for pre in sorted(preconditions):
                    domain += f" (not {pre})"
                domain += ")\n"
                domain += "  )\n\n"

        # Goal state actions for End Events
        for end_event in self.get_elements_by_type("End Event"):
            end_id = end_event.id
            name = end_event.name.replace(" ", "_") if end_event.name else end_id
            domain += f"  (:action goal_{name}\n"
            domain += f"    :precondition (and ({end_id}))\n"
            domain += f"    :effect (done)\n"
            domain += "  )\n\n"

        domain += ")"
        return domain, sorted(predicates)
    
    def generate_problem_files(self, bpmn_filename, start_events, predicates, domain_name="domain_name"):
        output_folder = os.path.join(os.getcwd(), bpmn_filename)
        os.makedirs(output_folder, exist_ok=True)

        not_flattened_folder = os.path.join(output_folder, "not_flattened")
        os.makedirs(not_flattened_folder, exist_ok=True)

        count = 0
        for start_event in start_events:
            count += 1
            problem_name = f"p0{count}"
            file_path = os.path.join(not_flattened_folder, f"{problem_name}.pddl")

            # Initial state: only start_event is true
            init_state = [f"({start_event})"]

            # Goal: done must be true
            goal_state = "(and (done))"

            # Group predicates by type (optional but cleaner)
            events = [p for p in predicates if "Event" in p]
            gateways = [p for p in predicates if "Gateway" in p]
            tasks = [p for p in predicates if "Activity" in p or "Task" in p]

            object_section = ""
            if tasks:
                object_section += "    " + " ".join(tasks) + " - task\n"
            if events:
                object_section += "    " + " ".join(events) + " - event\n"
            if gateways:
                object_section += "    " + " ".join(gateways) + " - gateway\n"

            # Construct problem file content
            problem_content = f"""(define (problem {problem_name}-bpmn-no-flatten)
    (:domain {domain_name})
    (:objects
    {object_section.strip()}
    )
    (:init {' '.join(init_state)})
    (:goal {goal_state})
    )
    """
            with open(file_path, 'w') as f:
                f.write(problem_content)



if __name__ == '__main__':
    file_path = 'bpmn_diagrams/place_order.bpmn'
    domain_name = "place_order_no_flatten"
    parser = BPMNParser(file_path)
    parser.parse()

    # Print all parsed elements
    parser.print_elements()

    # Generate and print the PDDL domain
    pddl_domain, predicates = parser.generate_pddl_domain(domain_name)

    # Extract the BPMN file name (without extension)
    bpmn_filename = os.path.splitext(os.path.basename(file_path))[0]

    # Create a new folder in the current directory
    output_folder = os.path.join(os.getcwd(), bpmn_filename)
    os.makedirs(output_folder, exist_ok=True)

    not_flattened_folder = os.path.join(output_folder, "not_flattened")
    os.makedirs(not_flattened_folder, exist_ok=True)

    # Save the PDDL domain inside the flattened folder
    output_file_path = os.path.join(not_flattened_folder, f"{bpmn_filename}_domain_no_flatten.pddl")
    with open(output_file_path, "w") as f:
        f.write(pddl_domain)
    print(f"\nPDDL domain saved to {output_file_path}")

    # Identify start and end events
    start_events = [e.id for e in parser.get_elements_by_type("Start Event")]
    end_events = [e.id for e in parser.get_elements_by_type("End Event")]

    # Call the new generate_problem_files method
    parser.generate_problem_files(bpmn_filename, start_events, predicates, domain_name)
    print(f"Problem files generated in '{os.path.join(not_flattened_folder, 'problems')}'")