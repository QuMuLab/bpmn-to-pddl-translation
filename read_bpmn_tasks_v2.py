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
        merged_tasks = set()
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
            if "Inclusive Gateway" in e.type and len(outgoing.get(e.id, [])) > 1:
                gw_id = sanitize_name(e.id)
                domain += f"    (at_least_one_branch_{gw_id})\n"
                predicates.add(f"at_least_one_branch_{gw_id}")
                for tgt in outgoing[e.id]:
                    branch_id = sanitize_name(f"{e.id}_{tgt}")
                    domain += f"    (branch_started_{branch_id})\n"
                    predicates.add(f"branch_started_{branch_id}")

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
                        domain += f"    :effect (and ({gateway_id}))\n"
                        domain += "  )\n\n"

        def map_converging_to_diverging():
            # Returns a dict { converging_id : diverging_id }
            result = {}
            for e in self.elements:
                if "Inclusive Gateway" in e.type and len(outgoing.get(e.id, [])) > 1:
                    # Found diverging gateway
                    diverging_id = e.id
                    # Traverse forward to find matching converging gateway(s)
                    visited = set()
                    queue = list(outgoing.get(e.id, []))
                    while queue:
                        current_id = queue.pop(0)
                        if current_id in visited:
                            continue
                        visited.add(current_id)
                        current_elem = elements_by_id.get(current_id)
                        if not current_elem:
                            continue
                        if "Inclusive Gateway" in current_elem.type and len(incoming.get(current_id, [])) > 1:
                            # Found matching converging gateway
                            result[current_id] = diverging_id
                        else:
                            queue.extend(outgoing.get(current_id, []))
            return result

        converge_to_diverge = map_converging_to_diverging()
        # Inclusive diverging gateway actions
        for e in self.elements:
            if "Inclusive Gateway" in e.type and len(outgoing.get(e.id, [])) > 1:
                gw_id = sanitize_name(e.id)
                domain += f"  (:action inclusive_diverge_{gw_id}\n"
                domain += f"    :precondition (and ({gw_id}))\n"
                domain += f"    :effect (and\n"
                
                for tgt in outgoing[e.id]:
                    tgt_id = sanitize_name(tgt)
                    branch_id = sanitize_name(f"{e.id}_{tgt}")
                    domain += f"      (oneof\n"
                    domain += f"        (and ({tgt_id}) (branch_started_{branch_id}) (at_least_one_branch_{gw_id}))\n"
                    domain += f"        (and)\n"
                    domain += f"      )\n"
                
                domain += f"      (not ({gw_id}))\n"
                domain += f"    )\n"
                domain += f"  )\n\n"

        # Inclusive converging gateway actions
        for e in self.elements:
            if "Inclusive Gateway" in e.type and len(incoming.get(e.id, [])) > 1:
                gw_id = sanitize_name(e.id)
                nexts = outgoing.get(e.id, [])
                if len(nexts) == 1:
                    next_id = sanitize_name(nexts[0])

                    # 🟢 Get diverging ID for this converging gateway
                    diverge_id = converge_to_diverge.get(e.id, e.id)
                    diverge_gw_id = sanitize_name(diverge_id)

                    # 🟢 Build preconditions
                    branch_conds = ' '.join(
                        f"(not (branch_started_{sanitize_name(f'{diverge_id}_{src_id}')}))"
                        for src_id in incoming[e.id]
                    )

                    domain += f"  (:action inclusive_converge_{gw_id}\n"
                    domain += f"    :precondition (and ({gw_id}) (at_least_one_branch_{diverge_gw_id}) {branch_conds})\n"
                    domain += f"    :effect (and ({next_id}) (not ({gw_id})))\n"
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
        
        # Identify converging gateways
        def is_converging_gateway(elem_id):
            elem = elements_by_id.get(elem_id)
            return elem and "Gateway" in elem.type and len(incoming.get(elem_id, [])) > 1
        
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
        
        # Handle Parallel Gateways
        for e in self.elements:
            if e.id in merged_tasks or e.id in skipped_gateways:
                continue
            if "Parallel Gateway" not in e.type:
                continue

            targets = outgoing.get(e.id, [])
            if len(targets) <= 1:
                continue  # Not a diverging parallel gateway

            paths = []
            converging_candidate = None

            for t in targets:
                path = []
                curr = t
                while True:
                    path.append(curr)
                    nexts = outgoing.get(curr, [])

                    # If this node is a converging gateway, stop here
                    if is_converging_gateway(curr):
                        converging_candidate = curr
                        break
                    if not nexts or len(nexts) > 1:
                        converging_candidate = None
                        break
                    curr = nexts[0]

                if not converging_candidate:
                    break
                paths.append(path)

            if not converging_candidate or len(paths) != len(targets):
                continue  # Not all paths converged properly

            post_converging = outgoing.get(converging_candidate, [])
            if len(post_converging) != 1:
                continue  # Not a clean single exit after convergence

            after_converging = post_converging[0]
            skipped_gateways.update({e.id, converging_candidate})

            # Collect intermediate tasks
            intermediate_tasks = set()
            for path in paths:
                for node_id in path[:-1]:  # Exclude the converging gateway itself
                    if "Task" in elements_by_id[node_id].type:
                        intermediate_tasks.add(node_id)

            # Diverging action
            diverge_name = sanitize_name(elements_by_id[e.id].name or e.id)
            domain += f"  (:action parallel_{diverge_name}\n"
            domain += f"    :precondition (and ({sanitize_name(e.id)}))\n"
            effects = [f"({sanitize_name(tgt)})" for tgt in targets]
            effects.append(f"({sanitize_name(converging_candidate)})")
            domain += f"    :effect (and {' '.join(effects)} (not ({sanitize_name(e.id)})))\n"
            domain += "  )\n\n"

            # Converging action
            converge_name = sanitize_name(elements_by_id[converging_candidate].name or converging_candidate)
            domain += f"  (:action parallel_{converge_name}\n"
            preconds = [f"({sanitize_name(converging_candidate)})"] + [f"(not ({sanitize_name(t)}))" for t in intermediate_tasks]
            domain += f"    :precondition (and {' '.join(preconds)})\n"
            domain += f"    :effect (and ({sanitize_name(after_converging)}) (not ({sanitize_name(converging_candidate)})))\n"
            domain += "  )\n\n"

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
                    effects = [f"({sanitize_name(tgt)})" for tgt in targets]
                    domain += f"  (:action {action_name}\n"
                    domain += f"    :precondition (and {precondition})\n"
                    domain += f"    :effect (and {' '.join(effects)} (not {precondition}))\n"
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

                    domain += f"  (:action {action_name}\n"
                    domain += f"    :precondition (and {precondition})\n"
                    domain += f"    :effect (and"

                    if len(oneof_effects) > 1:
                        domain += f" (oneof {' '.join(oneof_effects)})"
                    elif len(oneof_effects) == 1:
                        domain += f" {oneof_effects[0]}"

                    domain += f" (not {precondition}))\n"
                    domain += "  )\n\n"
                    generated.add(e.id)
                    continue

                else:
                    # Fallback for other gateways
                    if len(targets) == 1:
                        effect = f"({sanitize_name(targets[0])})"
                        domain += f"  (:action {action_name}\n"
                        domain += f"    :precondition (and {precondition})\n"
                        domain += f"    :effect (and {effect} (not {precondition}))\n"
                        domain += "  )\n\n"
                    elif len(targets) > 1:
                        effects = [f"({sanitize_name(tgt)})" for tgt in targets]
                        domain += f"  (:action {action_name}\n"
                        domain += f"    :precondition (and {precondition})\n"
                        domain += f"    :effect (and {' '.join(effects)} (not {precondition}))\n"
                        domain += "  )\n\n"
                    generated.add(e.id)
                    continue

            if "Task" in e.type:
                incoming_ids = incoming.get(e.id, [])
                merged_sources = set(get_merged_id(src_id) for src_id in incoming_ids)

                outgoing_targets = outgoing.get(e.id, [])
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

                        def get_preconds_for_source(task_id, src_id):
                            src_elem = elements_by_id.get(src_id)
                            if src_elem:
                                if src_elem.type == "Exclusive Gateway":
                                    return {f"({sanitize_name(task_id)})"}
                                elif "Event" in src_elem.type or "Gateway" in src_elem.type:
                                    return {f"({sanitize_name(src_id)})"}
                                else:
                                    return {f"({sanitize_name(src_id)})"}
                            return set()

                        preconditions = get_preconds_for_source(e.id, src_id)

                        # Add branch_started for inclusive branches
                        if src_elem and "Inclusive Gateway" in src_elem.type and len(outgoing.get(src_elem.id, [])) > 1:
                            branch_pred = f"branch_started_{sanitize_name(src_elem.id + '_' + e.id)}"
                            preconditions.add(f"({branch_pred})")

                        domain += f"  (:action {action_name}\n"
                        domain += f"    :precondition (and {' '.join(sorted(preconditions))})\n"
                        domain += f"    :effect (and"
                        if effects:
                            domain += f" {' '.join(sorted(set(effects)))}"
                        if oneof_effects:
                            unique_effects = list(dict.fromkeys(oneof_effects))
                            if len(unique_effects) == 1:
                                domain += f" {unique_effects[0]}"
                            else:
                                domain += f" (oneof {' '.join(unique_effects)})"
                        for pre in sorted(preconditions):
                            domain += f" (not {pre})"
                        domain += ")\n"
                        domain += "  )\n\n"
                else:
                    has_control_gateway = any(
                        elements_by_id.get(src_id) and
                        "Gateway" in elements_by_id[src_id].type and
                        ("Exclusive" in elements_by_id[src_id].type or "Parallel" in elements_by_id[src_id].type)
                        for src_id in incoming_ids
                    )

                    if has_control_gateway:
                        preconditions = {f"({sanitize_name(e.id)})"}
                    else:
                        preconditions = get_immediate_preconditions(e.id)

                    base_name = sanitize_name(e.name.replace(" ", "_")) if e.name else sanitize_name(e.id)
                    action_name = get_unique_action_name(base_name)

                    domain += f"  (:action {action_name}\n"
                    domain += f"    :precondition (and {' '.join(sorted(preconditions))})\n"
                    domain += f"    :effect (and"
                    if effects:
                        domain += f" {' '.join(sorted(set(effects)))}"
                    if oneof_effects:
                        unique_effects = list(dict.fromkeys(oneof_effects))
                        if len(unique_effects) == 1:
                            domain += f" {unique_effects[0]}"
                        else:
                            domain += f" (oneof {' '.join(unique_effects)})"
                    for pre in sorted(preconditions):
                        domain += f" (not {pre})"
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
        (:init)
        (:goal {goal_state})
        )
    """
        with open(empty_init_path, 'w') as f:
            f.write(p0_content)

        # Problem files for each start event
        for count, start_event in enumerate(start_events, 1):
            problem_name = f"p0{count}"
            file_path = os.path.join(not_flattened_folder, f"{problem_name}.pddl")

            init_state = [f"({start_event})"]
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
    file_path = 'bpmn_diagrams/dispatch_of_goods.bpmn'
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