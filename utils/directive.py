import re
import yaml

from typing import Any, Callable, Dict, List, Optional, Tuple


DIRECTIVE = re.compile(r"^\s*@(?P<directive>.*)\((?P<props>.*)\)\s*$", re.M)

ALL_DIRECTIVES: Dict[str, Callable] = {}


def directive(fn):
    ALL_DIRECTIVES[fn.__name__] = fn


def parse_directives(topic: str) -> List[Tuple[Callable, str]]:
    lines = DIRECTIVE.findall(topic)
    directives = []
    for [name, props] in lines:
        if fn := ALL_DIRECTIVES[name]:
            directives.append((fn, props))
    return directives


def parse_single(props: str) -> Optional[Any]:
    try:
        return yaml.load(props)
    except Exception:
        return None


def parse_multi(props: str) -> Optional[Dict[str, Any]]:
    return parse_single("{" + props + "}")
