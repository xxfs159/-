from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import generate_next_week_plan, identify_weak_points, load_all_data
from src.database import get_connection, init_db
from src.seed_data import seed_sample_data


def test_weak_points_and_plan():
    seed_sample_data(force=True)
    conn = get_connection()
    init_db(conn)
    data = load_all_data(conn)
    weak = identify_weak_points(data, top_n=3)
    plan = generate_next_week_plan(data)
    assert len(weak) > 0
    assert len(plan) >= 3
    assert "knowledge_point" in weak.columns
    conn.close()
