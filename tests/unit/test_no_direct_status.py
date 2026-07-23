# tests/unit/test_no_direct_status.py
"""Waechter: order.status darf nur in apps/orders/transitions.py gesetzt werden."""
import ast
from pathlib import Path

CMP_ROOT = Path(__file__).resolve().parents[2] / "cmp"
ALLOWED = {CMP_ROOT / "apps" / "orders" / "transitions.py"}


def _order_status_assignments(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if not (isinstance(target, ast.Attribute) and target.attr == "status"):
                continue
            base = target.value
            name = base.id if isinstance(base, ast.Name) else (
                base.attr if isinstance(base, ast.Attribute) else "")
            if "order" in name.lower():   # order.status, req.order.status, ...
                hits.append(node.lineno)
    return hits


def test_no_direct_order_status_assignment_outside_transitions():
    offenders = []
    files = list((CMP_ROOT / "apps").rglob("*.py")) + list(
        (CMP_ROOT / "core").rglob("*.py"))
    for path in files:
        if path in ALLOWED or "migrations" in path.parts:
            continue
        for lineno in _order_status_assignments(path):
            offenders.append(f"{path.relative_to(CMP_ROOT)}:{lineno}")
    assert not offenders, (
        "Direkte order.status-Zuweisung ausserhalb transitions.py:\n"
        + "\n".join(offenders)
    )
