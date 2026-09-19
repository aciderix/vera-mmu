"""La source MCP d'ARET, partagée par `C09`, `C10` et `C11` qui la citent tous les trois.

Ces trois couplages portent sur le même fichier — `aret_mmu_server.py` — et sur trois de ses
aspects : la doctrine statique qu'il embarque, les quarante-quatre outils qu'il écrit à la main, et
la racine unique qu'il impose. Le verser une fois et l'analyser ici évite trois copies qui
divergeraient, et surtout trois transcriptions de ce qu'il fait.
"""
from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path


REFERENCE = Path(__file__).resolve().parent / "fixtures" / "aret_v1" / "source" / "mcp_server_reference.py"
#: SHA-256 de `aret_mmu_server.py` dans `aciderix/ARET-MMU` au commit épinglé par le README.
REFERENCE_SHA256 = "9ba5a6584d9f292b5ae396e45d3c701a8f49bd5a9365a90ec089699672c7e936"


def tree() -> ast.Module:
    return ast.parse(REFERENCE.read_text(encoding="utf-8"))


def reference_digest() -> str:
    return sha256(REFERENCE.read_bytes()).hexdigest()


def tool_functions() -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Les outils `aret_*` que le serveur définit, extraits plutôt que comptés à la main."""
    return [
        node for node in tree().body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("aret_")
    ]


def tool_parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    return [argument.arg for argument in node.args.args + node.args.kwonlyargs]


def module_constant(name: str) -> ast.Constant | None:
    """Rendre la valeur d'une constante de module si — et seulement si — c'en est une."""
    for node in tree().body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.value if isinstance(node.value, ast.Constant) else None
    return None
