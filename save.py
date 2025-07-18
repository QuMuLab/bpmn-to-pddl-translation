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
        self.add_elements('inclusiveGateway', 'Inclusive Gateway')
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

        # Build outgoing map first for comparison
        outgoing_map = {}
        for flow in self.get_elements_by_type('Sequence Flow'):
            outgoing_map.setdefault(flow.sourceRef, []).append(flow.targetRef)

        for e in self.elements:
            if e.type in ['Sequence Flow', 'Message Flow', 'Parallel Gateway', 'Exclusive Gateway', 'Inclusive Gateway', 'Event-Based Gateway']:
                merged_elements.append(e)
                continue

            key = (e.type, e.name)
            e_outgoing = set(outgoing_map.get(e.id, []))

            # Find a previously seen element with same type, name, and outgoing targets
            match = None
            for seen_key, seen_elem in seen.items():
                if seen_key != key:
                    continue
                seen_outgoing = set(outgoing_map.get(seen_elem.id, []))
                if e_outgoing == seen_outgoing:
                    match = seen_elem
                    break

            if match is None:
                seen[key] = e
                merged_elements.append(e)
            else:
                primary = match
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
        skipped_gateways = set()

        def get_merged_id(element_id):
            return self.id_mapping.get(element_id, element_id)

        for flow in self.get_elements_by_type('Sequence Flow'):
            src = get_merged_id(flow.sourceRef)
            tgt = get_merged_id(flow.targetRef)
            outgoing.setdefault(src, []).append(tgt)
            incoming.setdefault(tgt, []).append(src)

        def sanitize_name(name):
            return re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        def is_valid_message_flow(source_elem, target_elem):
            # Only allow Task → Event or Event → Task
            if not source_elem or not target_elem:
                return False

            # One must be a task, the other must be an event
            is_source_task = "Task" in source_elem.type
            is_target_task = "Task" in target_elem.type
            is_source_event = "Event" in source_elem.type
            is_target_event = "Event" in target_elem.type

            if is_source_task and is_target_event:
                return True
            if is_source_event and is_target_task:
                return True

            return False

        synthetic_sequence_flows = []
        for e in self.elements:
            if e.type != 'Message Flow':
                continue

            source = elements_by_id.get(e.sourceRef)
            target = elements_by_id.get(e.targetRef)
            if not source or not target:
                continue

            # Only allow Task <-> Event message flows
            if ("Task" in source.type and "Event" in target.type) or ("Event" in source.type and "Task" in target.type):
                # Adjust Start Events as Intermediate Catch Events if needed
                if source.type == "Start Event":
                    source.type = "Intermediate Catch Event"
                if target.type == "Start Event":
                    target.type = "Intermediate Catch Event"

                # Add synthetic flow only for valid Task-Event pairs
                synthetic_sequence_flows.append(
                    BPMNElement(
                        "Sequence Flow",
                        e.id + "_from_msgflow",
                        e.name,
                        sourceRef=e.sourceRef,
                        targetRef=e.targetRef
                    )
                )

        # Now add ONLY these synthetic flows to self.elements and update incoming/outgoing:
        self.elements.extend(synthetic_sequence_flows)

        for flow in synthetic_sequence_flows:
            src = flow.sourceRef
            tgt = flow.targetRef
            outgoing.setdefault(src, []).append(tgt)
            incoming.setdefault(tgt, []).append(src)
        
        self.elements.extend(synthetic_sequence_flows)

        parallel_converging_gateways = {}

        for elem_id, elem in elements_by_id.items():
            if (
                "Parallel Gateway" in elem.type
                and len(incoming.get(elem_id, [])) > 1
            ):
                parallel_converging_gateways[elem_id] = [0,len(incoming.get(elem_id, []))]

        domain = f"(define (domain {domain_name})\n"
        domain += "  (:requirements :strips :typing)\n"
        domain += "  (:types task event gateway)\n\n"

        domain += "  (:predicates\n"
        for e in self.elements:
            if "Event" in e.type or "Gateway" in e.type or "Task" in e.type:
                pred = sanitize_name(e.id)
                if pred not in predicates:
                    domain += f"    ({pred})\n"
                    predicates.add(pred)

            if e.type == "Exclusive Gateway":
                for flow in self.get_elements_by_type("Sequence Flow"):
                    if flow.sourceRef == e.id:
                        pred = sanitize_name(flow.targetRef)
                        if pred not in predicates:
                            domain += f"    ({pred})\n"
                            predicates.add(pred)
        
        for e in self.elements:
            if "Inclusive Gateway" in e.type:
                gw_id = sanitize_name(e.id)
                n_outgoing = len(outgoing.get(e.id, []))
                n_incoming = len(incoming.get(e.id, []))

                if n_incoming == 1 and n_outgoing > 1:
                    # Diverging inclusive gateway: define the counter and triggers
                    for i in range(n_outgoing + 1):
                        counter_pred = f"inclusive_counter_{gw_id}_{i}"
                        domain += f"    ({counter_pred})\n"
                        predicates.add(counter_pred)

                    inc_pred = f"increase_{gw_id}"
                    dec_pred = f"decrease_{gw_id}"
                    domain += f"    ({inc_pred})\n"
                    domain += f"    ({dec_pred})\n"
                    domain += f"    (at_least_one_branch_{gw_id})\n"
                    predicates.add(inc_pred)
                    predicates.add(dec_pred)

                    for tgt in outgoing.get(e.id, []):
                        branch_id = sanitize_name(f"{gw_id}_{tgt}")
                        branch_pred = f"branch_started_{branch_id}"
                        domain += f"    ({branch_pred})\n"
                        predicates.add(branch_pred)

        for gw_id in parallel_converging_gateways.keys():
            incoming_count = parallel_converging_gateways[gw_id][1]
            for i in range(incoming_count):
                pred = f"({sanitize_name(gw_id)}_precondition_{i})"
                domain += f"    {pred}\n"
                predicates.add(pred[1:-1])

        domain += "    (done)\n"
        domain += "    (started)\n"
        domain += "  )\n\n"

        start_events = self.get_elements_by_type("Start Event")
        if len(start_events) == 1:
            start = start_events[0]
            start_id = sanitize_name(start.id)
            action_name = sanitize_name("start_" + (start.name or start.id))
            domain += f"  (:action {action_name}\n"
            domain += f"    :precondition (and (not (started))(not ({start_id})))\n"
            domain += f"    :effect (and ({start_id}) (started))\n"
            domain += "  )\n\n"
        elif len(start_events) > 1:
            start_preds = [sanitize_name(e.id) for e in start_events]
            domain += f"  (:action start_process\n"
            domain += f"    :precondition (and (not (started)) {' '.join(f'(not ({p}))' for p in start_preds)})\n"
            domain += f"    :effect (and (oneof {' '.join(f'({p})' for p in start_preds)}) (started))\n"
            domain += "  )\n\n"

        for e in self.elements:
            if "Gateway" in e.type:
                inc = incoming.get(e.id, [])
                if len(inc) == 1:
                    src_elem = elements_by_id.get(inc[0])
                    if src_elem and "Start Event" in src_elem.type:
                        start_id = sanitize_name(src_elem.id)
                        gateway_id = sanitize_name(e.id)
                        action_name = f"activate_{gateway_id}"
                        domain += f"  (:action {action_name}\n"
                        domain += f"    :precondition (and ({start_id}))\n"
                        domain += f"    :effect (and ({gateway_id}) (not({start_id})))\n"
                        domain += "  )\n\n"
        
        def get_parallel_gateway_precondition_if_needed(element_id, outgoing, parallel_converging_gateways):
            # Look at *all* outgoing edges from this element
            for target_id in outgoing.get(element_id, []):
                if target_id in parallel_converging_gateways:
                    counter, incoming_count = parallel_converging_gateways[target_id]
                    if counter >= incoming_count:
                        # Safety: don't exceed available counters
                        return ""
                    pred = f" ({sanitize_name(target_id)}_precondition_{counter})"
                    parallel_converging_gateways[target_id][0] += 1
                    return pred
            # If none of the outgoing edges go to a converging parallel gateway
            return ""


        def map_inclusive_gateway_pairs(elements, incoming, outgoing, start_events, sanitize_name):
            elements_by_id = {e.id: e for e in elements}
            result = {}

            for start in start_events:
                visited = set()
                stack = []
                queue = [start.id]

                while queue:
                    current_id = queue.pop(0)
                    if current_id in visited:
                        continue
                    visited.add(current_id)

                    current_elem = elements_by_id.get(current_id)
                    if not current_elem:
                        continue

                    # Check if it's an inclusive gateway
                    if "Inclusive Gateway" in current_elem.type:
                        n_incoming = len(incoming.get(current_id, []))
                        n_outgoing = len(outgoing.get(current_id, []))

                        if n_incoming == 1 and n_outgoing > 1:
                            # Diverging gateway
                            stack.append(current_id)
                        elif n_incoming > 1 and n_outgoing == 1:
                            # Converging gateway
                            if stack:
                                diverging_id = stack.pop()
                                converging_id = current_id
                                # Store both directions
                                result[sanitize_name(diverging_id)] = sanitize_name(converging_id)
                                result[sanitize_name(converging_id)] = sanitize_name(diverging_id)

                    # Traverse outgoing edges
                    for tgt in outgoing.get(current_id, []):
                        if tgt not in visited:
                            queue.append(tgt)

            return result
        
        def generate_inclusive_counter_actions(gateway_id, n):
            inc_pred = f"increase_{gateway_id}"
            dec_pred = f"decrease_{gateway_id}"
            lines = []

            # Increase action (descending order)
            lines.append(f"  (:action inclusive_increase_{gateway_id}")
            lines.append(f"    :precondition (and ({inc_pred}))")
            lines.append("    :effect (and")
            lines.append(f"      (not ({inc_pred}))")
            for i in reversed(range(n)):
                lines.append(f"      (when (inclusive_counter_{gateway_id}_{i}) (and (not (inclusive_counter_{gateway_id}_{i})) (inclusive_counter_{gateway_id}_{i+1})))")
            lines.append("    )")
            lines.append("  )\n")

            # Decrease action (ascending order)
            lines.append(f"  (:action inclusive_decrease_{gateway_id}")
            lines.append(f"    :precondition (and ({dec_pred}))")
            lines.append("    :effect (and")
            lines.append(f"      (not ({dec_pred}))")
            for i in range(1, n+1):
                lines.append(f"      (when (inclusive_counter_{gateway_id}_{i}) (and (not (inclusive_counter_{gateway_id}_{i})) (inclusive_counter_{gateway_id}_{i-1})))")
            lines.append("    )")
            lines.append("  )\n")

            return "\n".join(lines)

        converge_to_diverge = map_inclusive_gateway_pairs(
            self.elements,
            incoming,
            outgoing,
            start_events,
            sanitize_name
        )

        # Inclusive diverging gateway actions
        for e in self.elements:
            if "Inclusive Gateway" in e.type and len(incoming.get(e.id, [])) == 1 and len(outgoing.get(e.id, [])) > 1:
                gw_id = sanitize_name(e.id)
                num_branches = len(outgoing.get(e.id, []))

                # Add the increase/decrease counter actions for this gateway
                counter_actions = generate_inclusive_counter_actions(gw_id, num_branches)
                domain += counter_actions
                domain += "\n"

                # Now define the diverging gateway action itself
                domain += f"  (:action inclusive_diverge_{gw_id}\n"
                domain += f"    :precondition (and ({gw_id}))\n"
                domain += f"    :effect (and\n"
                
                for tgt in outgoing[e.id]:
                    tgt_id = sanitize_name(tgt)
                    domain += f"      (oneof\n"
                    domain += f"        (and ({tgt_id}) (increase_{gw_id}) (at_least_one_branch_{gw_id}) (not ({gw_id})))\n"
                    domain += f"        (and)\n"
                    domain += f"      )\n"
                
                domain += f"    )\n"
                domain += f"  )\n\n"

       # Inclusive converging gateway actions
        for e in self.elements:
            if "Inclusive Gateway" in e.type and len(incoming.get(e.id, [])) > 1:
                gw_id = sanitize_name(e.id)
                nexts = outgoing.get(e.id, [])
                if len(nexts) == 1:
                    next_id = sanitize_name(nexts[0])

                    # Get diverging ID for this converging gateway
                    diverge_id = converge_to_diverge.get(e.id, e.id)
                    diverge_gw_id = sanitize_name(diverge_id)

                    # Precondition needs:
                    # 1. The converging gateway itself active
                    # 2. At least one branch fired
                    # 3. The counter is 0
                    pred = get_parallel_gateway_precondition_if_needed(e.id,outgoing, parallel_converging_gateways)
                    domain += f"  (:action inclusive_converge_{gw_id}\n"
                    domain += f"    :precondition (and ({gw_id}) (at_least_one_branch_{diverge_gw_id}) (inclusive_counter_{diverge_gw_id}_0))\n"
                    domain += f"    :effect (and ({next_id}) (not ({gw_id})) (not (at_least_one_branch_{diverge_gw_id})){pred})\n"
                    domain += f"  )\n\n"

        def get_immediate_preconditions(element_id, override_src=None):
            preconditions = set()
            sources = [override_src] if override_src else incoming.get(element_id, [])

            for src_id in sources:
                src_elem = elements_by_id.get(src_id)
                if not src_elem:
                    continue

                src_name = sanitize_name(src_id)
                elem_name = sanitize_name(element_id)

                if src_elem.type == "Exclusive Gateway":
                    # Controlled by exclusive gateway, wait for the element itself
                    preconditions.add(f"({elem_name})")

                elif "Inclusive Gateway" in src_elem.type and len(outgoing.get(src_id, [])) > 1:
                    # Inclusive gateway with multiple branches, add branch_started predicate for this task
                    branch_pred = f"branch_started_{sanitize_name(src_id + '_' + element_id)}"
                    preconditions.add(f"({branch_pred})")

                    # Also require the task itself to be ready
                    preconditions.add(f"({elem_name})")

                elif "Event" in src_elem.type or "Gateway" in src_elem.type:
                    # Source event or gateway predicate
                    preconditions.add(f"({src_name})")

                else:
                    # Source is a task: wait for the task itself
                    preconditions.add(f"({elem_name})")

            # If no preconditions found, use the single start event if exists
            if not preconditions and len(start_events) == 1:
                preconditions.add(f"({sanitize_name(start_events[0].id)})")

            return preconditions
        
        used_action_names = {}
        def get_unique_action_name(base):
            count = used_action_names.get(base, 0)
            if count == 0:
                used_action_names[base] = 1
                return base
            else:
                used_action_names[base] += 1
                return f"{base}_{used_action_names[base]}"
            
        def get_effects_with_following_gateways(target_ids):
            effects = []
            for target_id in target_ids:
                branch_effects = {f"({sanitize_name(target_id)})"}  # Use set to avoid duplicates
                target_elem = elements_by_id.get(target_id)
                if target_elem and "Event" in target_elem.type:
                    for next_id in outgoing.get(target_id, []):
                        next_elem = elements_by_id.get(next_id)
                        if next_elem and "Gateway" in next_elem.type:
                            branch_effects.add(f"({sanitize_name(next_elem.id)})")  # add to set
                if len(branch_effects) == 1:
                    effects.append(next(iter(branch_effects)))  # only one predicate
                else:
                    effects.append(f"(and {' '.join(branch_effects)})")
            return effects

        generated = set()
        for e in self.elements:
            if e.id in skipped_gateways or e.id in generated:
                continue

            if "Start Event" in e.type or "End Event" in e.type or "Sequence Flow" in e.type:
                continue

            if "Gateway" in e.type and "Inclusive Gateway" not in e.type:
                targets = outgoing.get(e.id, [])
                precondition = f"({sanitize_name(e.id)})"
                if "Exclusive Gateway" in e.type:
                    prefix = "exclusive"
                elif "Parallel Gateway" in e.type:
                    prefix = "parallel"
                elif "Event-Based Gateway" in e.type:
                    prefix = "event"
                else:
                    prefix = "gateway"
                action_name = sanitize_name(f"{prefix}_{e.name or e.id}")

                if "Parallel Gateway" in e.type:
                    # Parallel gateway — activate all downstream tasks
                    pred = get_parallel_gateway_precondition_if_needed(e.id, outgoing, parallel_converging_gateways)

                    # Build preconditions for converging gateways
                    preconds = [f"({sanitize_name(e.id)})"]
                    if e.id in parallel_converging_gateways:
                        incoming_count = parallel_converging_gateways[e.id][1]
                        for i in range(incoming_count):
                            preconds.append(f"({sanitize_name(e.id)}_precondition_{i})")
                    else:
                        # Default precondition if not a converging gateway
                        preconds = [f"({sanitize_name(e.id)})"]

                    # Build effects
                    effects = [f"({sanitize_name(tgt)})" for tgt in targets]

                    domain += f"  (:action {action_name}\n"
                    domain += f"    :precondition (and {' '.join(preconds)})\n"
                    domain += f"    :effect (and {' '.join(effects)} (not ({sanitize_name(e.id)})){pred})\n"
                    domain += "  )\n\n"

                    generated.add(e.id)
                    continue

                elif "Exclusive Gateway" in e.type or "Event-Based Gateway" in e.type:
                    oneof_effects = []

                    for tgt in targets:
                        effect_predicates = [f"({sanitize_name(tgt)})"]

                        # Check if the immediate successor of this target is a gateway
                        if "Event-Based Gateway" in e.type:
                            next_flows = [flow for flow in self.get_elements_by_type("Sequence Flow") if flow.sourceRef == tgt]
                            for flow in next_flows:
                                next_elem = elements_by_id.get(flow.targetRef)
                                if next_elem and "Gateway" in next_elem.type:
                                    effect_predicates.append(f"({sanitize_name(next_elem.id)})")

                        if len(effect_predicates) == 1:
                            oneof_effects.append(effect_predicates[0])
                        else:
                            oneof_effects.append(f"(and {' '.join(effect_predicates)})")
                    pred = get_parallel_gateway_precondition_if_needed(e.id,outgoing, parallel_converging_gateways)
                    domain += f"  (:action {action_name}\n"
                    domain += f"    :precondition (and {precondition})\n"
                    domain += f"    :effect (and"

                    if len(oneof_effects) > 1:
                        domain += f" (oneof {' '.join(oneof_effects)})"
                    elif len(oneof_effects) == 1:
                        domain += f" {oneof_effects[0]}"

                    domain += f" (not {precondition}){pred})\n"
                    domain += "  )\n\n"
                    generated.add(e.id)
                    continue

                else:
                    # Fallback for other gateways
                    if len(targets) == 1:
                        effect = f"({sanitize_name(targets[0])})"
                        domain += f"  (:action {action_name}\n"
                        domain += f"    :precondition (and {precondition})\n"
                        domain += f"    :effect (and {effect} (not {precondition}){pred})\n"
                        domain += "  )\n\n"
                    elif len(targets) > 1:
                        effects = [f"({sanitize_name(tgt)})" for tgt in targets]
                        domain += f"  (:action {action_name}\n"
                        domain += f"    :precondition (and {precondition})\n"
                        domain += f"    :effect (and {' '.join(effects)} (not {precondition}){pred})\n"
                        domain += "  )\n\n"
                    generated.add(e.id)
                    continue
            
            if "Task" in e.type:
                incoming_ids = [
                    src_id for src_id in incoming.get(e.id, [])
                    if is_valid_message_flow(elements_by_id.get(src_id), e) or "SequenceFlow" in src_id
                ]

                merged_sources = set(get_merged_id(src_id) for src_id in incoming_ids)

                outgoing_targets = [
                    tgt_id for tgt_id in outgoing.get(e.id, [])
                    if is_valid_message_flow(e, elements_by_id.get(tgt_id)) or True  # Always include all?
                ]
                effects = []
                oneof_effects_set = set()

                if len(outgoing_targets) == 1:
                    effects = get_effects_with_following_gateways(outgoing_targets)
                elif len(outgoing_targets) > 1:
                    for target_id in outgoing_targets:
                        branch_effects = [f"({sanitize_name(target_id)})"]
                        target_elem = elements_by_id.get(target_id)
                        if target_elem and "Event" in target_elem.type:
                            for next_id in outgoing.get(target_id, []):
                                next_elem = elements_by_id.get(next_id)
                                if next_elem and "Gateway" in next_elem.type:
                                    branch_effects.append(f"({sanitize_name(next_elem.id)})")
                        effect_str = f"(and {' '.join(branch_effects)})" if len(branch_effects) > 1 else branch_effects[0]
                        oneof_effects_set.add(effect_str)

                oneof_effects = sorted(oneof_effects_set)

                # Detect inclusive gateway sources
                inclusive_branch_sources = []
                for src_id in incoming_ids:
                    src_elem = elements_by_id.get(src_id)
                    if src_elem and "Inclusive Gateway" in src_elem.type and len(outgoing.get(src_elem.id, [])) > 1:
                        inclusive_branch_sources.append(src_elem.id)

                if len(merged_sources) > 1:
                    for src_id in incoming_ids:
                        src_elem = elements_by_id.get(src_id)
                        if not src_elem:
                            continue

                        suffix = sanitize_name(src_elem.id)
                        base_name = f"{sanitize_name(e.name or e.id)}_from_{suffix}"
                        action_name = get_unique_action_name(base_name)

                        # Build preconditions
                        standard_preconditions = set()
                        branch_markers = set()

                        # Add normal predecessor preconditions
                        if src_elem:
                            if src_elem.type == "Exclusive Gateway":
                                standard_preconditions.add(f"({sanitize_name(e.id)})")
                            elif "Event" in src_elem.type or "Gateway" in src_elem.type:
                                standard_preconditions.add(f"({sanitize_name(src_elem.id)})")
                            else:
                                standard_preconditions.add(f"({sanitize_name(src_elem.id)})")

                        # Inclusive diverging predecessor handling
                        if src_elem and "Inclusive Gateway" in src_elem.type and len(outgoing.get(src_elem.id, [])) > 1:
                            branch_marker = f"branch_started_{sanitize_name(src_elem.id + '_' + e.id)}"
                            branch_markers.add(branch_marker)

                        pred = get_parallel_gateway_precondition_if_needed(e.id,outgoing, parallel_converging_gateways)

                        # Start writing the action
                        domain += f"  (:action {action_name}\n"
                        domain += f"    :precondition (and {' '.join(sorted(standard_preconditions))}"
                        for marker in sorted(branch_markers):
                            domain += f" (not {marker})"
                        domain += ")\n"

                        # Add branch_started effects
                        for marker in sorted(branch_markers):
                            domain += f" ({marker})"

                        domain += f"    :effect (and"

                        # Add normal effects
                        if effects:
                            domain += f" {' '.join(sorted(set(effects)))}{pred}"

                        # Check if task has an outgoing message flow
                        has_msgflow = any(
                            f.type == "Message Flow" and f.sourceRef == e.id
                            for f in self.get_elements_by_type("Message Flow")
                        )

                        # Handle effects
                        if oneof_effects:
                            unique_effects = list(dict.fromkeys(oneof_effects))
                            if has_msgflow:
                                # Conjunctive activation for tasks with message flow
                                domain += f" {' '.join(unique_effects)}{pred}"
                            elif len(unique_effects) == 1:
                                domain += f" {unique_effects[0]}{pred}"
                            else:
                                domain += f" (oneof {' '.join(unique_effects)}{pred})"

                        # Remove standard preconditions
                        for pre in sorted(standard_preconditions):
                            domain += f" (not {pre})"

                        # Add branch_started effects
                        for marker in sorted(branch_markers):
                            domain += f" ({marker})"

                        # Check if any immediate outgoing target is a converging Inclusive Gateway
                        for tgt_id in outgoing.get(e.id, []):
                            tgt_elem = elements_by_id.get(tgt_id)
                            if tgt_elem and "Inclusive Gateway" in tgt_elem.type and len(incoming.get(tgt_elem.id, [])) > 1:
                                diverging_id = converge_to_diverge.get(tgt_elem.id)
                                if diverging_id:
                                    diverge_gw_id = sanitize_name(diverging_id)
                                    domain += f" (decrease_{diverge_gw_id})"

                        domain += ")\n"
                        domain += "  )\n\n"

                else:
                    # Check if any predecessor is an Exclusive or Parallel Gateway (control gateway)
                    has_control_gateway = any(
                        elements_by_id.get(src_id) and
                        "Gateway" in elements_by_id[src_id].type and
                        ("Exclusive" in elements_by_id[src_id].type or "Parallel" in elements_by_id[src_id].type)
                        for src_id in incoming_ids
                    )

                    # Start with only the task itself as precondition
                    branch_preconditions = set()
                    branch_effects = set()
                    pred = get_parallel_gateway_precondition_if_needed(e.id,outgoing, parallel_converging_gateways)

                    if has_control_gateway:
                        # After Exclusive/Parallel gateway: only the task itself as precondition
                        standard_preconditions = {f"({sanitize_name(e.id)})"}
                    else:
                        # Normal case: inherit predecessors as preconditions
                        standard_preconditions = get_immediate_preconditions(e.id)

                    # For each predecessor, check for diverging inclusive gateways to add branch markers
                    for src_id in incoming_ids:
                        src_elem = elements_by_id.get(src_id)
                        if not src_elem:
                            continue

                        if "Inclusive Gateway" in src_elem.type and len(outgoing.get(src_elem.id, [])) > 1:
                            branch_name = f"branch_started_{sanitize_name(src_elem.id + '_' + e.id)}"
                            branch_preconditions.add(f"(not ({branch_name}))")
                            branch_effects.add(f"({branch_name})")
                        # Do NOT add gateway predecessors to standard preconditions

                    base_name = sanitize_name(e.name.replace(" ", "_")) if e.name else sanitize_name(e.id)
                    action_name = get_unique_action_name(base_name)

                    # ---------------------------------
                    # Determine if immediately after diverging inclusive gateway
                    inclusive_diverge_src = None
                    counter_levels_increase = None
                    for src_id in incoming.get(e.id, []):
                        src_elem = elements_by_id.get(src_id)
                        if src_elem and "Inclusive Gateway" in src_elem.type and len(outgoing.get(src_elem.id, [])) > 1:
                            inclusive_diverge_src = src_elem
                            counter_levels_increase = len(outgoing.get(src_elem.id, []))
                            break

                    # Determine if immediately before converging inclusive gateway
                    inclusive_converge_tgt = None
                    counter_levels_decrease = None
                    for tgt_id in outgoing.get(e.id, []):
                        tgt_elem = elements_by_id.get(tgt_id)
                        if tgt_elem and "Inclusive Gateway" in tgt_elem.type and len(incoming.get(tgt_elem.id, [])) > 1:
                            inclusive_converge_tgt = tgt_elem
                            diverging_id = converge_to_diverge.get(tgt_elem.id)
                            if diverging_id:
                                diverge_elem = elements_by_id.get(diverging_id)
                                if diverge_elem:
                                    counter_levels_decrease = len(outgoing.get(diverge_elem.id, []))
                            break

                    # ---------------------------------
                    # Write the action
                    domain += f"  (:action {action_name}\n"
                    extra_preconditions = set()
                    if inclusive_diverge_src:
                        diverge_gw_id = sanitize_name(inclusive_diverge_src.id)
                        extra_preconditions.add(f"(not (inclusive_counter_{diverge_gw_id}_0))")
                    # Make sure no positive branch_started in standard_preconditions
                    standard_preconditions = {
                        p for p in standard_preconditions
                        if not any(be.strip("()") in p for be in branch_effects)
                    }

                    all_preconditions = sorted(standard_preconditions | branch_preconditions | extra_preconditions)
                    domain += f"    :precondition (and {' '.join(all_preconditions)})\n"
                    domain += f"    :effect (and"

                    # Add normal effects
                    if effects:
                        domain += f" {' '.join(sorted(set(effects)))}{pred}"

                    if oneof_effects:
                        unique_effects = list(dict.fromkeys(oneof_effects))
                        
                        # Check if task has an outgoing message flow
                        has_msgflow = any(
                            f.type == "Message Flow" and f.sourceRef == e.id
                            for f in self.get_elements_by_type("Message Flow")
                        )

                        if has_msgflow:
                            # Conjunctive activation for tasks with message flow
                            domain += f" {' '.join(unique_effects)}{pred}"
                        elif len(unique_effects) == 1:
                            domain += f" {unique_effects[0]}{pred}"
                        else:
                            domain += f" (oneof {' '.join(unique_effects)}{pred})"

                    # ---------------------------------
                    # Add *REMOVE* precondition for tasks + branch markers + increase counter if immediately after diverging inclusive gateway
                    if inclusive_diverge_src:
                        # Remove task precondition
                        for pre in sorted(standard_preconditions):
                            domain += f" (not {pre})"

                        # Add branch_started effects
                        for branch in sorted(branch_effects):
                            domain += f" {branch}"

                    else:
                        # Remove the task itself (but not branch markers)
                        for pre in sorted(standard_preconditions):
                            domain += f" (not {pre})"

                    for tgt_id in outgoing.get(e.id, []):
                        tgt_elem = elements_by_id.get(tgt_id)
                        if tgt_elem and "Inclusive Gateway" in tgt_elem.type and len(incoming.get(tgt_elem.id, [])) > 1:
                            diverging_id = converge_to_diverge.get(tgt_elem.id)
                            if diverging_id:
                                diverge_gw_id = sanitize_name(diverging_id)
                                domain += f" (decrease_{diverge_gw_id})"
                    domain += ")\n"
                    domain += "  )\n\n"

        # End events
        for end_event in self.get_elements_by_type("End Event"):
            end_id = sanitize_name(end_event.id)
            name = sanitize_name(end_event.name or end_event.id)
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

        # Deduplicate predicates
        predicates = set(predicates)

        # Track inclusive_counter_*_0 predicates
        initial_counters = sorted(p for p in predicates if p.startswith("inclusive_counter_") and p.endswith("_0"))

        # Remove branch_started_* and at_least_one_branch_* from task/gateway/event classification
        marker_preds = {p for p in predicates if p.startswith("branch_started_") or p.startswith("at_least_one_branch_")}
        non_marker_preds = predicates - marker_preds

        # Classify non-marker preds
        gateways = {p for p in non_marker_preds if "Gateway" in p}
        events = {p for p in non_marker_preds if "Event" in p}
        tasks = {p for p in non_marker_preds if "Activity" in p or "Task" in p}

        # Remove overlap: gateway > event > task
        events -= gateways
        tasks -= (gateways | events)

        # Step 2: Build object section
        object_section = ""
        if tasks:
            object_section += "    " + " ".join(sorted(tasks)) + " - task\n"
        if events:
            object_section += "    " + " ".join(sorted(events)) + " - event\n"
        if gateways:
            object_section += "    " + " ".join(sorted(gateways)) + " - gateway\n"

        # Shared goal
        goal_state = "(and (done))"

        # Problem 0 (no start events initialized)
        empty_init_path = os.path.join(not_flattened_folder, "p0.pddl")
        p0_content = f"""(define (problem p0-bpmn-no-flatten)
        (:domain {domain_name})
        (:objects
{object_section.strip()}
        )
        (:init {' '.join(f'({c})' for c in initial_counters)})
        (:goal {goal_state})
        )
"""

        with open(empty_init_path, 'w') as f:
            f.write(p0_content)

        # Problem files for each start event
        for count, start_event in enumerate(start_events, 1):
            problem_name = f"p0{count}"
            file_path = os.path.join(not_flattened_folder, f"{problem_name}.pddl")

            init_state = [f"({start_event})"] + [f"({c})" for c in initial_counters]
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
    file_path = 'bpmn_diagrams/self_serve_restaurant.bpmn'
    domain_name = file_path.split("/")[1][:-5]
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

    # Identify start events
    start_events = [e.id for e in parser.get_elements_by_type("Start Event")]

    # Call the new generate_problem_files method
    parser.generate_problem_files(bpmn_filename, start_events, predicates, domain_name)
    print(f"Problem files generated in '{os.path.join(not_flattened_folder, 'problems')}'")