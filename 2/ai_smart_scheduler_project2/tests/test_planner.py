from datetime import date

import pandas as pd

from src.planner import generate_plan, plan_to_dataframe, rows_to_tasks


def test_generate_plan_with_sample_data():
    course_df = pd.read_csv("data/sample_courses.csv")
    task_df = pd.read_csv("data/sample_tasks.csv")
    free_df = pd.read_csv("data/sample_free_slots.csv")

    tasks = rows_to_tasks(task_df)
    plan, warnings = generate_plan(tasks, course_df, free_df, start_day=date(2026, 5, 11), days=7)
    plan_df = plan_to_dataframe(plan)

    assert not plan_df.empty
    assert "任务" in plan_df.columns
    assert len(warnings) >= 0
