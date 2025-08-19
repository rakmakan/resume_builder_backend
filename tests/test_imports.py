import pathlib, sys
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.models import CandidateProfile
from app.graph import graph
from app.cli import main as cli_main


def test_imports():
    profile = CandidateProfile(name="Alice", years_experience=5, skills=["python"])
    assert profile.name == "Alice"
    assert graph.get_nodes()  # graph has nodes registered
    assert callable(cli_main)
