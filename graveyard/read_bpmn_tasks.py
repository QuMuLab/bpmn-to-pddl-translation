import xml.etree.ElementTree as ET
import html
import os
import itertools

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

    def print_elements(self):
        for element in self.elements:
            print(element)
            print()

    def get_elements_by_type(self, element_type):
        return [e for e in self.elements if e.type == element_type]

    def flatten_diagram(self):
        elements_by_id = {e.id: e for e in self.elements}
        incoming_flows = {}
        outgoing_flows = {}
        for flow in self.get_elements_by_type('Sequence Flow'):
            incoming_flows.setdefault(flow.targetRef, []).append(flow)
            outgoing_flows.setdefault(flow.sourceRef, []).append(flow)

        next_id_suffix = 1
        new_elements = []

        def duplicate_subgraph(element_id, id_suffix):
            nonlocal next_id_suffix
            original_elem = elements_by_id[element_id]
            new_id = f"{element_id}_dup{id_suffix}"

            new_elem = BPMNElement(
                original_elem.type,
                new_id,
                f"{original_elem.name} copy {id_suffix}" if original_elem.name else None
            )
            new_elements.append(new_elem)

            for out_flow in outgoing_flows.get(element_id, []):
                new_flow_id = f"{out_flow.id}_dup{next_id_suffix}"
                next_id_suffix += 1
                new_flow = BPMNElement(
                    out_flow.type,
                    new_flow_id,
                    out_flow.name,
                    sourceRef=new_id,
                    targetRef=None
                )
                target_id = out_flow.targetRef
                new_target_id = duplicate_subgraph(target_id, id_suffix)
                new_flow.targetRef = new_target_id
                new_elements.append(new_flow)

            return new_id

        for target_id, flows in incoming_flows.items():
            if len(flows) > 1:
                for i, flow in enumerate(flows[1:], start=1):
                    new_target_id = duplicate_subgraph(target_id, next_id_suffix)
                    flow.targetRef = new_target_id
                    next_id_suffix += 1

        self.elements.extend(new_elements)

    def generate_pddl_domain(self, domain_name="bpmn-generated"):
        # Map elements for quick access
        elements_by_id = {e.id: e for e in self.elements}
        outgoing = {}  # {source_id: [target_ids]}
        incoming = {}  # {target_id: [source_ids]}

        for flow in self.get_elements_by_type('Sequence Flow'):
            outgoing.setdefault(flow.sourceRef, []).append(flow.targetRef)
            incoming.setdefault(flow.targetRef, []).append(flow.sourceRef)

        domain = f"(define (domain {domain_name})\n"
        domain += "  (:requirements :strips :typing)\n"
        domain += "  (:types task event gateway)\n\n"

        # Predicates
        domain += "  (:predicates\n"
        for e in self.elements:
            if "Event" in e.type or "Gateway" in e.type:
                domain += f"    (event-{e.id})\n"
        domain += "  )\n\n"

        # Helper to get immediate preconditions
        def get_immediate_preconditions(element_id):
            preconditions = set()
            for src_id in incoming.get(element_id, []):
                src_elem = elements_by_id.get(src_id)
                if src_elem and ("Event" in src_elem.type or "Gateway" in src_elem.type):
                    preconditions.add(f"(event-{src_id})")
            # Fallback: if no preconditions, use start event
            if not preconditions:
                start_events = self.get_elements_by_type('StartEvent')
                if start_events:
                    start_id = start_events[0].id
                    preconditions.add(f"(event-{start_id})")
            return preconditions

        # Generate actions for tasks and gateways
        for e in self.elements:
            if "Task" in e.type or "Gateway" in e.type:
                preconditions = get_immediate_preconditions(e.id)

                # Gateways must include their own event predicate
                if "Gateway" in e.type:
                    preconditions.add(f"(event-{e.id})")

                # Determine effects
                outgoing_targets = outgoing.get(e.id, [])
                if len(outgoing_targets) == 1:
                    effects = [f"(event-{outgoing_targets[0]})"]
                    oneof_effects = []
                elif len(outgoing_targets) > 1:
                    effects = []
                    oneof_effects = [f"(event-{target_id})" for target_id in outgoing_targets]
                else:
                    effects = []
                    oneof_effects = []

                action_name = e.name.replace(" ", "_") if e.name else e.id
                domain += f"  (:action {action_name}\n"
                domain += f"    :precondition (and {' '.join(sorted(preconditions))})\n"
                domain += f"    :effect (and"
                if effects:
                    domain += f" {' '.join(sorted(effects))}"
                if oneof_effects:
                    domain += f" (oneof {' '.join(sorted(oneof_effects))})"
                domain += ")\n"
                domain += "  )\n\n"

        domain += ")"
        return domain
    
    def generate_problem_files(self, bpmn_filename, start_events, end_events, domain_name="domain_name"):
        output_folder = os.path.join(os.getcwd(), bpmn_filename)
        os.makedirs(output_folder, exist_ok=True)

        flattened_folder = os.path.join(output_folder, "flattened")
        os.makedirs(flattened_folder, exist_ok=True)

        count = 0
        for start_event, end_event in itertools.product(start_events, end_events):
            count += 1
            problem_name = f"p0{count}"
            file_path = os.path.join(flattened_folder, f"{problem_name}.pddl")

            # Initial state: all false except start_event
            init_state = [start_event]

            # Goal: end_event should be true
            goal_state = f"(and ({end_event}))"

            problem_content = f"""(define (problem p{count}-bpmn-flatten)
  (:domain {domain_name})
  (:init {' '.join(init_state)})
  (:goal {goal_state})
)
"""
            with open(file_path, 'w') as f:
                f.write(problem_content)

if __name__ == '__main__':
    file_path = 'bpmn_diagrams/order_pizza.bpmn'
    domain_name = "pizza_order_flatten"
    parser = BPMNParser(file_path)
    parser.parse()
    parser.flatten_diagram()

    # Print all parsed elements
    parser.print_elements()

    # Generate and print the PDDL domain
    pddl_domain = parser.generate_pddl_domain(domain_name)

    # Extract the BPMN file name (without extension)
    bpmn_filename = os.path.splitext(os.path.basename(file_path))[0]

    # Create a new folder in the current directory
    output_folder = os.path.join(os.getcwd(), bpmn_filename)
    os.makedirs(output_folder, exist_ok=True)

    flattened_folder = os.path.join(output_folder, "flattened")
    os.makedirs(flattened_folder, exist_ok=True)

    # Save the PDDL domain inside the flattened folder
    output_file_path = os.path.join(flattened_folder, f"{bpmn_filename}_domain.pddl")
    with open(output_file_path, "w") as f:
        f.write(pddl_domain)
    print(f"\nPDDL domain saved to {output_file_path}")

    # Identify start and end events
    start_events = [e.id for e in parser.get_elements_by_type("Start Event")]
    end_events = [e.id for e in parser.get_elements_by_type("End Event")]

    # Call the new generate_problem_files method
    parser.generate_problem_files(bpmn_filename, start_events, end_events, domain_name)
    print(f"Problem files generated in '{os.path.join(flattened_folder, 'problems')}'")