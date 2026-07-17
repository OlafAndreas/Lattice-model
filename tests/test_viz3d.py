"""Tests for the 3D lattice visualization data builder."""

from lattice.viz3d import build_lattice3d_data


def test_lattice3d_data_shape():
    data = build_lattice3d_data()
    knowns, empties = data["knowns"], data["empties"]

    # 17 particles collapse into occupied v2 cells: the 3 neutrinos share
    # one cell, and photon+gluon share one (no force flags in v2).
    assert sum(len(k["occupants"]) for k in knowns) == 17
    assert len(knowns) == 14
    assert len(empties) == 1410

    for k in knowns:
        assert set(k) >= {"spin", "q", "m", "st", "occupants", "fam"}
        assert 0 <= k["fam"] < 5
    for e in empties[:20]:
        assert set(e) >= {"spin", "q", "m", "st", "nov", "near"}
        assert e["nov"] > 0
        assert e["near"]


def test_lattice3d_graviton_cell_flagged():
    data = build_lattice3d_data()
    grav = [e for e in data["empties"] if e.get("graviton")]
    assert len(grav) == 1
    g = grav[0]
    assert (g["spin"], g["q"], g["m"], g["st"]) == (2.0, 0, -9, 1)
    assert g["near"] in ("photon", "gluon")


def test_lattice3d_family_labels():
    data = build_lattice3d_data()
    labels = data["family_labels"]
    assert len(labels) == 5
    fams_used = {k["fam"] for k in data["knowns"]}
    assert fams_used == set(range(5))


def test_lattice3d_hadron_layer():
    data = build_lattice3d_data()
    hk, he = data["hadrons"], data["hadron_empties"]

    # 42 curated hadrons collapse into occupied cells (flavor axes are
    # not part of the 3D coordinates, so e.g. Lambda/Sigma0/Xi0 share one).
    assert sum(len(k["occupants"]) for k in hk) == 42
    assert len(hk) < 42
    for k in hk:
        assert 0 <= k["mult"] < 5
        assert len(k["details"]) == len(k["occupants"])

    # empty hadron cells are aggregated over the collapsed flavor axes
    assert sum(e["count"] for e in he) == 860
    for e in he[:20]:
        assert e["count"] >= 1 and e["nov"] > 0 and e["near"]

    assert len(data["multiplet_labels"]) == 5


def test_lattice3d_gen4_predictions():
    data = build_lattice3d_data()
    g4 = data["gen4"]
    assert [p["label"] for p in g4] == ["ℓ₄", "b′", "t′"]
    for p in g4:
        assert p["m"] <= 6          # placement band clamped to the axis
        assert p["mass_mev"] > 0 and p["method"]
    t4 = g4[-1]
    assert t4["band_true"] == 7 and t4["m"] == 6  # ~62 TeV, beyond axis


def test_lattice3d_hadron_forward_predictions():
    data = build_lattice3d_data()
    preds = data["hadron_preds"]
    labels = {p["label"] for p in preds}
    assert {"Ξbb", "Ωbb", "Ξbc", "Ωbc", "Ξcc⁺", "Ωccc", "Ωbbb",
            "Ωcc✓"} == labels
    # isospin doublets contribute one marker per charge state
    assert len(preds) == 10
    for p in preds:
        assert p["mass_mev"] > 3000 and p["head"]


def test_lattice3d_planes_data():
    """Multiplet-plane panels: every known hadron and every candidate slot
    must land in exactly one (baryon, spin, charm, beauty) panel."""
    data = build_lattice3d_data()
    panels = data["planes"]
    assert len(panels) >= 8
    n_known = sum(len(c["knowns"]) for p in panels for c in p["cells"])
    n_slots = sum(len(c["slots"]) for p in panels for c in p["cells"])
    assert n_known == 42
    assert n_slots == 860
    decuplet = [p for p in panels
                if p["baryon"] == 1 and p["spin"] == 1.5
                and p["charm"] == 0 and p["beauty"] == 0]
    assert len(decuplet) == 1
    omega_cells = [c for c in decuplet[0]["cells"]
                   if c["S"] == -3 and c["q"] == -3 and c["knowns"]]
    assert len(omega_cells) == 1  # Ω⁻ sits at the decuplet corner
