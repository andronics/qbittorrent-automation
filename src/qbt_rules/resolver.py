"""
Reference and variable resolution for qBittorrent automation rules

Implements the resolver layer that provides:
- Variable substitution: ${vars.name} → value
- Reference expansion: $ref: conditions.name → condition structure
- Instance-scoped variable overrides
- Type-aware value substitution
- Circular dependency detection
"""

import copy
import re
from typing import Any, Dict, List, Optional, Set

from qbt_rules.errors import (
    CircularRefError,
    InvalidRefError,
    InvalidVariableError,
    UnknownRefError,
    UnknownVariableError,
)
from qbt_rules.logging import get_logger

logger = get_logger(__name__)

# Pattern for variable substitution: ${vars.name}
VAR_PATTERN = re.compile(r'\$\{(vars\.\w+)\}')


class RuleResolver:
    """
    Resolves references and variables in rules configuration

    Two-phase resolution:
    1. Reference expansion ($ref: path) - recursive structural replacement
    2. Variable substitution (${vars.name}) - type-aware value replacement

    Example:
        >>> refs = {
        ...     'vars': {'min_ratio': 1.0},
        ...     'conditions': {
        ...         'well-seeded': {
        ...             'all': [
        ...                 {'field': 'info.ratio', 'operator': '>=', 'value': '${vars.min_ratio}'}
        ...             ]
        ...         }
        ...     }
        ... }
        >>> resolver = RuleResolver(refs)
        >>> rule = {'conditions': [{'$ref': 'conditions.well-seeded'}]}
        >>> resolved = resolver.resolve_rule(rule)
        >>> # Result: conditions expanded and variables substituted
    """

    def __init__(
        self,
        refs: Dict[str, Any],
        instance_id: Optional[str] = None,
        instances: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize resolver with refs block and optional instance override

        Args:
            refs: The refs block from config (vars, conditions, actions)
            instance_id: Optional instance ID for scoped variable overrides (stub for future)
            instances: Optional instances dict for instance-scoped overrides (stub for future)
        """
        # Extract typed groups from refs
        self.vars = dict(refs.get('vars', {}))
        self.conditions = refs.get('conditions', {})
        self.actions = refs.get('actions', {})

        # Future: Apply instance-scoped overrides
        # Currently stubbed - instance_id and instances accepted but not used
        # This keeps the API ready for multi-instance support in future versions
        if instance_id and instances:
            instance = instances.get(instance_id, {})
            instance_refs = instance.get('refs', {})
            instance_vars = instance_refs.get('vars', {})
            self.vars.update(instance_vars)
            logger.debug(f"Applied instance '{instance_id}' variable overrides: {list(instance_vars.keys())}")

    def resolve_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fully resolve a rule: expand refs, then substitute variables

        Args:
            rule: Raw rule dictionary from config

        Returns:
            Resolved rule ready for evaluation

        Raises:
            InvalidRefError: Invalid reference path format
            UnknownRefError: Reference not found in refs
            InvalidVariableError: Invalid variable path format
            UnknownVariableError: Variable not found in refs.vars
            CircularRefError: Circular reference dependency detected
        """
        # Phase 1: Deep copy to avoid mutating original
        resolved = copy.deepcopy(rule)

        # Phase 2: Expand all $ref references (recursive)
        resolved = self._expand_refs(resolved, ref_stack=set(), allow_conditions=True, allow_actions=True)

        # Phase 3: Substitute all ${vars.*} variables (type-aware)
        resolved = self._substitute_vars(resolved)

        return resolved

    def _expand_refs(
        self,
        node: Any,
        ref_stack: Set[str],
        allow_conditions: bool = True,
        allow_actions: bool = True
    ) -> Any:
        """
        Recursively expand $ref references in a data structure

        Args:
            node: Current node being processed (dict, list, or scalar)
            ref_stack: Stack of reference paths to detect circular dependencies
            allow_conditions: Whether condition refs are allowed in this context
            allow_actions: Whether action refs are allowed in this context

        Returns:
            Node with all $ref references expanded
        """
        if isinstance(node, dict):
            # Check if this dict is a $ref node
            if '$ref' in node:
                ref_path = node['$ref']

                # Validate path format
                if not isinstance(ref_path, str) or '.' not in ref_path:
                    raise InvalidRefError(
                        ref_path=str(ref_path),
                        reason="Path must be in format 'group.name'"
                    )

                # Detect circular dependencies
                if ref_path in ref_stack:
                    raise CircularRefError(ref_path=ref_path, ref_stack=list(ref_stack))

                # Look up and expand reference
                expanded = self._lookup_ref(ref_path, allow_conditions, allow_actions)

                # Recursively expand the referenced content
                new_stack = ref_stack | {ref_path}
                return self._expand_refs(expanded, new_stack, allow_conditions, allow_actions)
            else:
                # Regular dict - recursively process each value
                return {
                    key: self._expand_refs(value, ref_stack, allow_conditions, allow_actions)
                    for key, value in node.items()
                }

        elif isinstance(node, list):
            # Recursively process each list item
            return [
                self._expand_refs(item, ref_stack, allow_conditions, allow_actions)
                for item in node
            ]

        else:
            # Scalar value - return as-is
            return node

    def _substitute_vars(self, node: Any) -> Any:
        """
        Recursively substitute ${vars.*} variables in a data structure

        Type-aware substitution:
        - If ${vars.x} is the entire string value → preserve original type
        - If ${vars.x} is embedded in string → interpolate as string

        Args:
            node: Current node being processed

        Returns:
            Node with all variables substituted
        """
        if isinstance(node, dict):
            return {key: self._substitute_vars(value) for key, value in node.items()}

        elif isinstance(node, list):
            return [self._substitute_vars(item) for item in node]

        elif isinstance(node, str):
            # Check if entire string is a single variable reference
            if node.startswith('${') and node.endswith('}') and node.count('${') == 1:
                # Extract variable path
                var_path = node[2:-1]  # Remove ${ and }
                # Preserve original type
                return self._resolve_var(var_path)

            # String with embedded variables - interpolate
            def replace_var(match):
                var_path = match.group(1)
                value = self._resolve_var(var_path)
                return str(value)

            return VAR_PATTERN.sub(replace_var, node)

        else:
            # Scalar non-string value - return as-is
            return node

    def _lookup_ref(self, ref_path: str, allow_conditions: bool, allow_actions: bool) -> Any:
        """
        Look up a reference by dot-notation path

        Args:
            ref_path: Reference path like 'conditions.private-tracker'
            allow_conditions: Whether condition refs are allowed
            allow_actions: Whether action refs are allowed

        Returns:
            Referenced structure

        Raises:
            InvalidRefError: Invalid path format or disallowed group
            UnknownRefError: Reference not found
        """
        parts = ref_path.split('.', 1)
        if len(parts) != 2:
            raise InvalidRefError(
                ref_path=ref_path,
                reason="Expected format 'group.name' (e.g., 'conditions.private-tracker')"
            )

        group, name = parts

        if group == 'conditions':
            if not allow_conditions:
                raise InvalidRefError(
                    ref_path=ref_path,
                    reason="Condition references not allowed in this context"
                )
            if name not in self.conditions:
                raise UnknownRefError(ref_path=ref_path, available_refs=list(self.conditions.keys()))
            return self.conditions[name]

        elif group == 'actions':
            if not allow_actions:
                raise InvalidRefError(
                    ref_path=ref_path,
                    reason="Action references not allowed in this context"
                )
            if name not in self.actions:
                raise UnknownRefError(ref_path=ref_path, available_refs=list(self.actions.keys()))
            return self.actions[name]

        else:
            raise InvalidRefError(
                ref_path=ref_path,
                reason=f"Unknown group '{group}'. Valid groups: conditions, actions"
            )

    def _resolve_var(self, var_path: str) -> Any:
        """
        Resolve a variable by dot-notation path

        Args:
            var_path: Variable path like 'vars.min_ratio'

        Returns:
            Variable value (preserving original type)

        Raises:
            InvalidVariableError: Invalid path format
            UnknownVariableError: Variable not found
        """
        parts = var_path.split('.', 1)
        if len(parts) != 2 or parts[0] != 'vars':
            raise InvalidVariableError(
                var_path=var_path,
                reason="Expected format 'vars.name' (e.g., 'vars.min_ratio')"
            )

        name = parts[1]
        if name not in self.vars:
            raise UnknownVariableError(var_name=name, available_vars=list(self.vars.keys()))

        return self.vars[name]
