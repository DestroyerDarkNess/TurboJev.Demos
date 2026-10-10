"""Integrity regressions using scripted responses, not model-quality tests."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import snake


class ScriptedEngine:
    def __init__(self, choice):
        self.choice = choice
        self.requests = []

    def evaluate(self, request):
        self.requests.append(request)
        return {
            "answers": {
                "move": {
                    "type": "choice",
                    "choice": self.choice,
                    "probabilities": {"left": 0.9, "right": 0.1},
                }
            }
        }


class DecisionIntegrityTests(unittest.TestCase):
    def test_sensors_report_immediate_collisions_without_selecting_a_move(self):
        req = snake.make_move_request([(6, 0), (6, 1)], "up", (11, 0), "sensors")
        self.assertEqual(
            req["state"],
            "Food direction: right.\nBlocked directions: up, down.\nClear directions: left, right.",
        )
        self.assertEqual(set(req["questions"]["move"]["criteria"]), set(snake.DIRECTIONS))

    def test_sensors_keep_the_vacating_tail_clear(self):
        req = snake.make_move_request([(1, 1), (1, 2), (0, 2), (0, 1)], "up", (4, 4), "sensors")
        self.assertIn("Clear directions: up, left, right.", req["state"])

    def test_bad_but_valid_choice_is_not_replaced_by_better_probabilities(self):
        engine = ScriptedEngine("right")
        move, decision, _ = snake.jev_choose_move(engine, [(6, 5), (5, 5)], "right", (2, 5))
        self.assertEqual(move, "right")
        after, ate, collision = snake.apply_move([(6, 5), (5, 5)], "right", (2, 5), move)
        self.assertEqual(after[0], (7, 5))
        self.assertFalse(ate)
        self.assertIsNone(collision)
        self.assertEqual(decision["response"]["answers"]["move"]["choice"], move)

    def test_walls_do_not_filter_or_force_the_model_options(self):
        engine = ScriptedEngine("up")
        move, _, _ = snake.jev_choose_move(engine, [(0, 0), (1, 0)], "left", (4, 2))
        self.assertEqual(len(engine.requests), 1)
        criteria = engine.requests[0]["questions"]["move"]["criteria"]
        self.assertEqual(set(criteria), {"up", "down", "left", "right"})
        self.assertEqual(move, "up")
        self.assertEqual(
            snake.apply_move([(0, 0), (1, 0)], "left", (4, 2), move)[2], "model hit a wall"
        )

    def test_invalid_choice_fails_instead_of_falling_back(self):
        with self.assertRaisesRegex(RuntimeError, "No fallback"):
            snake.jev_choose_move(ScriptedEngine("diagonal"), [(6, 5), (5, 5)], "right", (2, 5))

    def test_reversal_is_a_failure_not_a_host_selected_move(self):
        self.assertEqual(
            snake.apply_move([(6, 5), (5, 5)], "right", (2, 5), "left")[2],
            "model selected a direct reversal",
        )

    def test_vacating_tail_is_not_a_collision(self):
        after, ate, collision = snake.apply_move(
            [(1, 1), (1, 2), (0, 2), (0, 1)], "up", (4, 4), "left"
        )
        self.assertEqual(after[0], (0, 1))
        self.assertFalse(ate)
        self.assertIsNone(collision)

    def test_trace_records_the_actual_response_and_applied_motion(self):
        engine = ScriptedEngine("up")
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            with (
                patch.object(snake, "HAS_RICH", False),
                patch.object(snake, "console", None),
                patch.object(snake, "draw_legacy"),
                patch.object(snake.time, "sleep"),
                patch.object(snake, "spawn_food", return_value=(8, 5)),
                patch("builtins.print"),
            ):
                summary = snake.play(engine, "scripted-test", 1, 0, "none", 0, trace)
            entry = json.loads(trace.read_text().splitlines()[1])
            self.assertEqual(entry["model_choice"], entry["applied_choice"])
            self.assertEqual(entry["response"]["answers"]["move"]["choice"], "up")
            self.assertEqual(entry["snake_after"][0], [6, 4])
            self.assertEqual(entry["request"], engine.requests[0])
            self.assertEqual(summary["model_decisions"], summary["executed_steps"])
            self.assertEqual(summary["host_selected_moves"], 0)


if __name__ == "__main__":
    unittest.main()
