"""
Normalization Utilities

Common algorithms for database normalization:
- Armstrong's axiom-based candidate key discovery
- Functional dependency analysis
- 3NF decomposition

This module is shared between evaluation and physical_design packages.
"""
from itertools import combinations
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict


def compute_closure(base_set: Set[str], deps: List[Tuple[Set[str], Set[str]]]) -> Set[str]:
    """
    Compute the closure of an attribute set under a set of functional dependencies.
    
    Using Armstrong's axioms to find all attributes that can be determined
    from the base_set given the functional dependencies.
    
    Args:
        base_set: Initial set of attributes
        deps: List of (determinant, dependents) tuples representing functional dependencies
        
    Returns:
        Set of all attributes in the closure
        
    Example:
        >>> deps = [({'A'}, {'B'}), ({'B'}, {'C'})]
        >>> compute_closure({'A'}, deps)
        {'A', 'B', 'C'}
    """
    closure = set(base_set)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in deps:
            if lhs <= closure and not rhs <= closure:
                closure.update(rhs)
                changed = True
    return closure


def find_candidate_keys(attrs: List[str], deps: List[Tuple[Set[str], Set[str]]]) -> List[Set[str]]:
    """
    Find all candidate keys for a relation using Armstrong's axioms.
    
    A candidate key is a minimal set of attributes whose closure equals
    all attributes of the relation.
    
    Args:
        attrs: List of all attributes in the relation
        deps: List of functional dependencies as (determinant, dependents) tuples
        
    Returns:
        List of candidate keys (each is a set of attributes)
        
    Example:
        >>> attrs = ['A', 'B', 'C']
        >>> deps = [({'A'}, {'B', 'C'})]
        >>> find_candidate_keys(attrs, deps)
        [{'A'}]
    """
    def is_candidate_key(candidate: Set[str], deps: List, all_attributes: Set[str]) -> bool:
        return compute_closure(candidate, deps) == all_attributes

    all_attributes = set(attrs)
    candidates = []
    
    # Try combinations from smallest to largest
    for i in range(1, len(attrs) + 1):
        for combo in combinations(attrs, i):
            candidate = set(combo)
            if is_candidate_key(candidate, deps, all_attributes):
                # Check if any subset is already a candidate key (minimality)
                if any(all(sub in candidate for sub in c) for c in candidates):
                    continue
                candidates.append(candidate)
    
    return candidates


def get_attribute_keys_by_armstrong(dependencies_json: Dict[str, Dict[str, List[str]]]) -> Tuple[Dict[str, List[str]], Dict[str, List[Set[str]]]]:
    """
    Identify primary keys for all entities based on functional dependencies using Armstrong's axioms.
    
    Args:
        dependencies_json: Dictionary of {entity_name: {determinant: [dependents]}}
        
    Returns:
        Tuple of:
        - attributes_all: Dictionary of all attributes per entity
        - candidate_keys_dict: Dictionary of candidate keys per entity
        
    Example:
        >>> deps = {"Student": {"ID": ["Name", "Age"]}}
        >>> attrs, keys = get_attribute_keys_by_armstrong(deps)
        >>> print(keys["Student"])
        [{'ID'}]
    """
    attributes_all = {}
    dependencies_all = {}
    
    for entity_name, entity in dependencies_json.items():
        attributes = []
        dependencies = []
        
        for depend_key in entity:
            # Handle composite determinants (separated by & or ,)
            if '&' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split('&')]
            elif ',' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split(',')]
            else:
                depend_key_list = [depend_key]
            
            # Collect all attributes
            attributes.extend(list(set(depend_key_list) | set(entity[depend_key])))
            dependencies.append((set(depend_key_list), set(entity[depend_key])))
        
        attributes = list(set(attributes))
        attributes_all[entity_name] = attributes
        dependencies_all[entity_name] = dependencies

    # Find candidate keys for each entity
    candidate_keys_dict = {}
    for entity_name in attributes_all:
        candidate_keys = find_candidate_keys(
            attributes_all[entity_name], 
            dependencies_all[entity_name]
        )
        candidate_keys_dict[entity_name] = candidate_keys
    
    return attributes_all, candidate_keys_dict


def get_attribute_keys_by_armstrong_single(attributes: List[str], dependencies: Dict[str, List[str]]) -> List[Set[str]]:
    """
    Find candidate keys for a single entity/relation.
    
    Args:
        attributes: List of all attributes
        dependencies: Dictionary of {determinant: [dependents]}
        
    Returns:
        List of candidate keys
    """
    dependencies_list = []
    for depend_key in dependencies:
        if '&' in depend_key:
            depend_key_list = [it.strip() for it in depend_key.split('&')]
        elif ',' in depend_key:
            depend_key_list = [it.strip() for it in depend_key.split(',')]
        else:
            depend_key_list = [depend_key]
        dependencies_list.append((set(depend_key_list), set(dependencies[depend_key])))
    
    return find_candidate_keys(attributes, dependencies_list)


def decompose_to_3nf(
    entity_fd_json: Dict[str, Dict[str, List[str]]], 
    entity_primary_keys: Dict[str, List[Set[str]]],
    attributes_all: Dict[str, List[str]] = None
) -> Dict[str, Dict[str, List[Set[str]]]]:
    """
    Decompose relations to Third Normal Form (3NF).
    
    Identifies partial and transitive dependencies and decomposes relations
    to eliminate them.
    
    Args:
        entity_fd_json: Functional dependencies {entity: {determinant: [dependents]}}
        entity_primary_keys: Primary keys {entity: [candidate_key_sets]}
        attributes_all: Optional attribute list per entity (computed if not provided)
        
    Returns:
        Dictionary of decomposition results {entity: {"decompose_relationships": [relations]}}
    """
    def parse_dependencies(entity_fd_json: Dict) -> List[Tuple]:
        """Parse functional dependencies into list format."""
        functional_dependencies = []
        for entity, dependencies in entity_fd_json.items():
            for determinant, dependents in dependencies.items():
                determinant_list = [attr.strip() for attr in determinant.split(",")]
                functional_dependencies.append((determinant_list, dependents, entity))
        return functional_dependencies

    def find_closure_local(dependencies: List, target_set: List) -> Set:
        """Calculate closure of attribute set."""
        closure = set(target_set)
        changed = True
        while changed:
            changed = False
            for X, Y in dependencies:
                if set(X).issubset(closure) and not set(Y).issubset(closure):
                    closure.update(Y)
                    changed = True
        return closure

    functional_dependencies = parse_dependencies(entity_fd_json)
    results_by_entity = defaultdict(lambda: {"decompose_relationships": []})
    
    # Classify dependencies by entity
    dependencies_by_entity = defaultdict(list)
    for determinant, dependent, entity in functional_dependencies:
        dependencies_by_entity[entity].append((determinant, dependent))

    for entity, deps in dependencies_by_entity.items():
        primary_keys = entity_primary_keys.get(entity, [])
        relations = []

        # Check for partial dependencies
        for X, Y in deps:
            closure = find_closure_local(dependencies_by_entity[entity], X)
            
            if any(set(X).issubset(pk) for pk in primary_keys):
                if not set(Y).issubset(closure):
                    partial_relation = set(X) | set(Y)
                    if partial_relation not in relations:
                        relations.append(partial_relation)

        # Check for transitive dependencies
        for X, Y in deps:
            if set(Y).issubset(find_closure_local(dependencies_by_entity[entity], X)):
                relation = set(X) | set(Y)
                if relation not in relations:
                    relations.append(relation)

        # Ensure primary key is preserved
        for pk in primary_keys:
            if not any(set(pk).issubset(relation) for relation in relations):
                relations.append(set(pk))

        # Remove duplicates and single-attribute relations
        unique_relations = []
        for rel in relations:
            if len(rel) > 1 and rel not in unique_relations:
                unique_relations.append(rel)

        results_by_entity[entity]["decompose_relationships"] = unique_relations

    return dict(results_by_entity)


def get_common_elements(list1: List, list2: List) -> List:
    """
    Get common elements between two lists.
    
    Args:
        list1: First list
        list2: Second list
        
    Returns:
        List of common elements
    """
    return list(set(list1).intersection(set(list2)))
