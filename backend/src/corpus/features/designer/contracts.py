from routedeck_core.contracts.navigation import NodeRef

from .schemas import DesignContent
from .topology import DesignTopology, compile_design_topology

DESIGNER_HOME_REF = NodeRef(id="designer.home")

__all__ = [
    "DESIGNER_HOME_REF",
    "DesignContent",
    "DesignTopology",
    "compile_design_topology",
]
