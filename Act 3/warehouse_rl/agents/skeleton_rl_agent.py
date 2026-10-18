#!/usr/bin/env python3
"""Optimization agent for staffing, order assignment, and warehouse layout."""

import numpy as np
from typing import Dict

from .standardized_agents import BaselineAgent
try:
    from ..environment.employee import EmployeeState
except ImportError:
    from environment.employee import EmployeeState


class SkeletonOptimizationAgent(BaselineAgent):
    """Use demand, worker productivity, and product movement data to optimize profit."""

    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        self.env._unlimited_hiring = True
        self.performance_metrics = []
        self.decision_history = []
        self.action_history = []
        self.reward_history = []
        self.staffing_parameters = {
            "hire_threshold_ratio": 3.0,
            "fire_threshold_ratio": 2.0,
            "profit_threshold": 0,
        }
        self.last_layout_check = -100
        self.layout_interval = 100
        self.max_workers = 8

    def reset(self):
        self.action_history = []
        self.reward_history = []
        self.last_layout_check = -self.layout_interval

    def get_action(self, observation: Dict) -> Dict:
        current_timestep = int(observation["time"][0])
        action = {
            "staffing_action": self._get_staffing_action(
                observation["financial"], observation["employees"]
            ),
            "layout_swap": self._get_layout_action(current_timestep),
            "order_assignments": self._get_order_assignments(),
        }
        self.action_history.append(action.copy())
        return action

    def _get_staffing_action(self, financial_state, employee_info) -> int:
        workers = [employee for employee in self.env.employees if not employee.is_manager]
        has_manager = any(employee.is_manager for employee in self.env.employees)
        queue_length = len(self.env.order_queue.orders)

        if not has_manager and self.env.current_timestep == 0:
            return 3

        worker_count = len(workers)
        queue_pressure = queue_length / max(1, worker_count)
        if (worker_count < self.max_workers and
                queue_pressure > self.staffing_parameters["hire_threshold_ratio"]):
            return 1

        if (worker_count > 5 and
                queue_pressure < self.staffing_parameters["fire_threshold_ratio"] and
                float(financial_state[0]) > self.staffing_parameters["profit_threshold"] and
                self.env.current_timestep % 100 == 0):
            slowest = min(workers, key=lambda employee: employee.base_speed_multiplier)
            if slowest.state == EmployeeState.IDLE:
                return 2
        return 0

    def _get_layout_action(self, current_timestep) -> list:
        if current_timestep - self.last_layout_check < self.layout_interval:
            return [0, 0]
        self.last_layout_check = current_timestep

        manager = next(
            (employee for employee in self.env.employees
             if employee.is_manager and employee.state == EmployeeState.IDLE),
            None,
        )
        if manager is None:
            return [0, 0]

        grid = self.env.warehouse_grid
        frequencies = np.asarray(grid.item_access_frequency, dtype=float)
        active = frequencies[frequencies > 0]
        if active.size == 0:
            return [0, 0]

        threshold = float(np.percentile(active, 75))
        hot_items = [
            item for item, frequency in enumerate(frequencies)
            if frequency >= threshold and frequency > 0
        ]
        storage_positions = [
            (x, y) for x, y in grid.storage_positions
            if grid.item_grid[y, x] >= 0
        ]

        best_swap = None
        best_benefit = 0.0
        for item_type in hot_items:
            for source in grid.find_item_locations(item_type):
                for target in storage_positions:
                    if source == target:
                        continue
                    target_item = int(grid.item_grid[target[1], target[0]])
                    benefit = self._layout_swap_benefit(
                        item_type, source, target_item, target, frequencies
                    )
                    if benefit > best_benefit:
                        best_benefit = benefit
                        best_swap = [
                            source[1] * grid.width + source[0],
                            target[1] * grid.width + target[0],
                        ]
        return best_swap if best_swap is not None else [0, 0]

    def _layout_swap_benefit(self, source_item, source, target_item, target, frequencies):
        grid = self.env.warehouse_grid
        delivery_positions = getattr(grid, "truck_bay_positions", [grid.packing_station])

        def delivery_distance(position):
            return min(
                grid.manhattan_distance(position, delivery)
                for delivery in delivery_positions
            )

        current_cost = frequencies[source_item] * delivery_distance(source)
        new_cost = frequencies[source_item] * delivery_distance(target)
        if target_item >= 0:
            current_cost += frequencies[target_item] * delivery_distance(target)
            new_cost += frequencies[target_item] * delivery_distance(source)

        for other_item in range(grid.num_item_types):
            cooccurrence = grid.item_cooccurrence[source_item, other_item]
            if cooccurrence <= 0 or other_item == target_item:
                continue
            locations = grid.find_item_locations(other_item)
            if locations:
                current_cost += cooccurrence * grid.manhattan_distance(source, locations[0])
                new_cost += cooccurrence * grid.manhattan_distance(target, locations[0])
        return current_cost - new_cost

    def _get_order_assignments(self) -> list:
        assignments = [0] * 20
        idle_workers = [
            (index, employee) for index, employee in enumerate(self.env.employees)
            if not employee.is_manager and employee.state == EmployeeState.IDLE
        ]
        orders = [
            (index, order) for index, order in enumerate(self.env.order_queue.orders[:20])
            if order.status == "pending"
        ]
        if not idle_workers or not orders:
            return assignments

        orders.sort(
            key=lambda pair: (-pair[1].value, -len(pair[1].items), pair[1].arrival_time)
        )
        idle_workers.sort(key=lambda pair: -pair[1].base_speed_multiplier)
        for (order_index, order), (employee_index, employee) in zip(orders, idle_workers):
            item_locations = [
                location
                for item in order.items
                for location in self.env.warehouse_grid.find_item_locations(item)
            ]
            if item_locations:
                assignments[order_index] = employee_index + 1
        return assignments

    def record_reward(self, reward: float):
        self.reward_history.append(reward)

    def should_update_policy(self) -> bool:
        return len(self.action_history) % 50 == 0

    def get_performance_metrics(self) -> Dict:
        if not self.reward_history:
            return {"avg_reward": 0, "total_actions": len(self.action_history)}
        return {
            "avg_reward": float(np.mean(self.reward_history[-100:])),
            "total_actions": len(self.action_history),
            "recent_performance": float(np.mean(self.reward_history[-10:])),
        }


def create_skeleton_optimization_agent(env) -> SkeletonOptimizationAgent:
    return SkeletonOptimizationAgent(env)


class StudentOptimizationAgent(SkeletonOptimizationAgent):
    """Compatibility alias for assignments that import the student class."""

