from __future__ import annotations

import contextlib
import sys

import numpy as np
import numpy.typing as npt
import pytest
from networkx import Graph
from networkx.utils import graphs_equal

from graphix.clifford import Clifford
from graphix.fundamentals import Plane
from graphix.graphsim.graphstate import GraphState
from graphix.graphsim.utils import convert_rustworkx_to_networkx, is_graphs_equal
from graphix.ops import Ops
from graphix.sim.statevec import Statevec

with contextlib.suppress(ModuleNotFoundError):
    from rustworkx import PyGraph


def get_state(g) -> Statevec:
    node_list = list(g.nodes)
    nqubit = len(g.nodes)
    gstate = Statevec(nqubit=nqubit)
    imapping = {node_list[i]: i for i in range(nqubit)}
    mapping = [node_list[i] for i in range(nqubit)]
    for i, j in g.edges:
        gstate.entangle((imapping[i], imapping[j]))
    for i in range(nqubit):
        if g.nodes[mapping[i]]["sign"]:
            gstate.evolve_single(Ops.Z, i)
    for i in range(nqubit):
        if g.nodes[mapping[i]]["loop"]:
            gstate.evolve_single(Ops.S, i)
    for i in range(nqubit):
        if g.nodes[mapping[i]]["hollow"]:
            gstate.evolve_single(Ops.H, i)
    return gstate


def meas_op(angle, vop=0, plane=Plane.XY, choice=0) -> npt.NDArray:
    """Return the projection operator for given measurement angle and local Clifford op (VOP).

    .. seealso:: :mod:`graphix.clifford`

    Parameters
    ----------
    angle : float
        original measurement angle in radian
    vop : int
        index of local Clifford (vop), see graphq.clifford.CLIFFORD
    plane : 'XY', 'YZ' or 'ZX'
        measurement plane on which angle shall be defined
    choice : 0 or 1
        choice of measurement outcome. measured eigenvalue would be (-1)**choice.

    Returns
    -------
    op : numpy array
        projection operator

    """
    assert vop in np.arange(24)
    assert choice in [0, 1]
    if plane == Plane.XY:
        vec = (np.cos(angle), np.sin(angle), 0)
    elif plane == Plane.YZ:
        vec = (0, np.cos(angle), np.sin(angle))
    elif plane == Plane.XZ:
        vec = (np.cos(angle), 0, np.sin(angle))
    op_mat = np.eye(2, dtype=np.complex128) / 2
    for i in range(3):
        op_mat += (-1) ** (choice) * vec[i] * Clifford(i + 1).matrix / 2
    return Clifford(vop).conj.matrix @ op_mat @ Clifford(vop).matrix


@pytest.mark.parametrize(
    "use_rustworkx",
    [
        False,
        pytest.param(
            True,
            marks=pytest.mark.skipif(sys.modules.get("rustworkx") is None, reason="rustworkx not installed"),
        ),
    ],
)
class TestGraphSim:
    def test_fig2(self, use_rustworkx: bool) -> None:
        """Three single-qubit measurements presented in Fig.2 of M. Elliot et al (2010)."""
        nqubit = 6
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        g = GraphState(nodes=np.arange(nqubit), edges=edges, use_rustworkx=use_rustworkx)
        gstate = get_state(g)
        g.measure_x(0)
        gstate.evolve_single(meas_op(0), [0])  # x meas
        gstate.normalize()
        gstate.remove_qubit(0)
        gstate2 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate2.flatten())) == pytest.approx(1)

        g.measure_y(1, choice=0)
        gstate.evolve_single(meas_op(0.5 * np.pi), [0])  # y meas
        gstate.normalize()
        gstate.remove_qubit(0)
        gstate2 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate2.flatten())) == pytest.approx(1)

        g.measure_z(3)
        gstate.evolve_single(meas_op(0.5 * np.pi, plane=Plane.YZ), 1)  # z meas
        gstate.normalize()
        gstate.remove_qubit(1)
        gstate2 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate2.flatten())) == pytest.approx(1)

    def test_e2(self, use_rustworkx: bool) -> None:
        nqubit = 6
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        g = GraphState(nodes=np.arange(nqubit), edges=edges, use_rustworkx=use_rustworkx)
        g.h(3)
        gstate = get_state(g)

        g.equivalent_graph_e2(3, 4)
        gstate2 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate2.flatten())) == pytest.approx(1)

        g.equivalent_graph_e2(4, 0)
        gstate3 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate3.flatten())) == pytest.approx(1)

        g.equivalent_graph_e2(4, 5)
        gstate4 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate4.flatten())) == pytest.approx(1)

        g.equivalent_graph_e2(0, 3)
        gstate5 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate5.flatten())) == pytest.approx(1)

        g.equivalent_graph_e2(0, 3)
        gstate6 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate6.flatten())) == pytest.approx(1)

    def test_e1(self, use_rustworkx: bool) -> None:
        nqubit = 6
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        g = GraphState(nodes=np.arange(nqubit), edges=edges, use_rustworkx=use_rustworkx)
        g.nodes[3]["loop"] = True
        gstate = get_state(g)
        g.equivalent_graph_e1(3)

        gstate2 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate2.flatten())) == pytest.approx(1)
        g.z(4)
        gstate = get_state(g)
        g.equivalent_graph_e1(4)
        gstate2 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate2.flatten())) == pytest.approx(1)
        g.equivalent_graph_e1(4)
        gstate3 = get_state(g)
        assert np.abs(np.dot(gstate.flatten().conjugate(), gstate3.flatten())) == pytest.approx(1)

    def test_local_complement(self, use_rustworkx: bool) -> None:
        nqubit = 6
        edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
        exp_edges = [(0, 1), (1, 2), (0, 2), (2, 3), (3, 4), (4, 0)]
        g = GraphState(nodes=np.arange(nqubit), edges=edges, use_rustworkx=use_rustworkx)
        g.local_complement(1)
        exp_g = GraphState(nodes=np.arange(nqubit), edges=exp_edges)
        assert is_graphs_equal(g, exp_g)


@pytest.mark.skipif(sys.modules.get("rustworkx") is None, reason="rustworkx not installed")
class TestGraphSimUtils:
    def test_is_graphs_equal_nx_nx(self) -> None:
        nnode = 6
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        g1 = GraphState(nodes=range(nnode), edges=edges, use_rustworkx=True)
        g2 = GraphState(nodes=range(nnode), edges=edges, use_rustworkx=True)
        assert is_graphs_equal(g1, g2)

    def test_is_graphs_equal_nx_rx(self) -> None:
        nnode = 6
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        g1 = GraphState(nodes=range(nnode), edges=edges, use_rustworkx=True)
        g2 = GraphState(nodes=range(nnode), edges=edges, use_rustworkx=True)
        assert is_graphs_equal(g1, g2)

    def test_is_graphs_equal_rx_nx(self) -> None:
        nnode = 6
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        g1 = GraphState(nodes=range(nnode), edges=edges, use_rustworkx=True)
        g2 = GraphState(nodes=range(nnode), edges=edges, use_rustworkx=True)
        assert is_graphs_equal(g1, g2)

    def test_is_graphs_equal_rx_rx(self) -> None:
        nnode = 6
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        g1 = GraphState(nodes=range(nnode), edges=edges, use_rustworkx=True)
        g2 = GraphState(nodes=range(nnode), edges=edges, use_rustworkx=True)
        assert is_graphs_equal(g1, g2)

    def test_convert_rustworkx_to_networkx(self) -> None:
        nnode = 6
        data = {"dummy": 1}
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        g_nx = Graph()
        g_nx.add_nodes_from(list(zip(range(nnode), [data] * nnode)))
        g_nx.add_edges_from(edges)
        g_rx = PyGraph()
        g_rx.add_nodes_from(list(zip(range(nnode), [data] * nnode)))
        g_rx.add_edges_from_no_data(edges)
        g_rx = convert_rustworkx_to_networkx(g_rx)
        assert graphs_equal(g_nx, g_rx)

    def test_convert_rustworkx_to_networkx_throw_error(self) -> None:
        nnode = 6
        edges = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]
        g_rx = PyGraph()
        g_rx.add_nodes_from(range(nnode))
        g_rx.add_edges_from_no_data(edges)
        with pytest.raises(TypeError):
            g_rx = convert_rustworkx_to_networkx(g_rx)
