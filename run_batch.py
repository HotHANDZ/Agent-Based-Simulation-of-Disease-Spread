# RUN MANY HEADLESS ITERATIONS, SAVE ONE AGGREGATED CSV, AND PLOT A SUMMARY PNG.
"""Batch runner for scenario.py with cross-iteration averages and a PNG report."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime

import matplotlib.pyplot as plt

import scenario
from simulation import Simulation


def _safe_mean(values: list[float]) -> float:
    return (sum(values) / len(values)) if values else 0.0


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(values)
    q = max(0.0, min(1.0, q))
    pos = q * (len(ordered) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return float(ordered[lo] * (1.0 - frac) + ordered[hi] * frac)


def _compute_new_infections(infected_series: list[int]) -> list[int]:
    # Approximate per-step incidence as positive increases in active infected count.
    if not infected_series:
        return []
    series = [infected_series[0]]
    for idx in range(1, len(infected_series)):
        delta = infected_series[idx] - infected_series[idx - 1]
        series.append(max(0, delta))
    return series


def _build_variable_definitions_text() -> str:
    return "\n".join(
        [
            "Scenario variables:",
            f"- num_agents={scenario.num_agents}",
            f"- initial_infected_count={scenario.initial_infected_count}",
            f"- population_vaccinated_fraction={scenario.population_vaccinated_fraction}",
            f"- bedridden={scenario.bedridden}",
            f"- width={scenario.width}, height={scenario.height}",
            f"- timesteps={scenario.timesteps}",
            f"- hours_per_timestep={scenario.hours_per_timestep}",
            f"- movement_units_per_hour={scenario.movement_units_per_hour}",
            f"- movement_distance_per_step={scenario.movement_distance_per_step}",
            f"- infectious_period_days={scenario.infectious_period_days}",
            f"- transmission_prob={scenario.transmission_prob}",
            f"- vaccine_transmission_risk_reduction_fraction={scenario.vaccine_transmission_risk_reduction_fraction}",
            f"- contact_radius={scenario.contact_radius}",
            f"- disease_preset={scenario.disease_preset}",
        ]
    )


def _write_aggregated_csv(path: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("No batch rows to write.")
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _build_summary_png(
    output_path: str,
    avg_infected_by_day: list[float],
    p25_infected_by_day: list[float],
    p75_infected_by_day: list[float],
    avg_total_infections: float,
    avg_total_recoveries: float,
    avg_infections_per_hour: float,
    avg_infections_per_day: float,
    total_days_defined: float,
    iterations: int,
    avg_peak_infected: float,
    p25_peak_infected: float,
    p75_peak_infected: float,
    avg_time_to_peak_day: float,
    avg_attack_rate_percent: float,
    avg_outbreak_duration_days: float,
    major_outbreak_probability_percent: float,
    avg_infection_burden_auc: float,
    avg_recovery_efficiency: float,
) -> None:
    parent = os.path.dirname(os.path.abspath(output_path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1.0])

    ax_day = fig.add_subplot(gs[0, 0])
    x_days = list(range(1, len(avg_infected_by_day) + 1))
    ax_day.plot(x_days, avg_infected_by_day, color="#3366cc", linewidth=2)
    ax_day.fill_between(
        x_days,
        p25_infected_by_day,
        p75_infected_by_day,
        color="#8fb4ff",
        alpha=0.35,
        label="IQR (25th-75th)",
    )
    ax_day.set_title("Average Infected Count Per Day")
    ax_day.set_xlabel("Simulation Day")
    ax_day.set_ylabel("Avg Infected Agents")
    ax_day.grid(alpha=0.3)
    ax_day.legend(loc="upper right")

    ax_text = fig.add_subplot(gs[0, 1])
    ax_text.axis("off")
    summary_text = "\n".join(
        [
            "Batch Summary",
            f"- Iterations: {iterations}",
            f"- Avg infections/hour: {avg_infections_per_hour:.3f}",
            f"- Avg infections/day: {avg_infections_per_day:.3f}",
            f"- Total days defined per iteration: {total_days_defined:.3f}",
            f"- Avg total infections: {avg_total_infections:.3f}",
            f"- Avg total recoveries: {avg_total_recoveries:.3f}",
            f"- Peak infected avg (IQR): {avg_peak_infected:.3f} ({p25_peak_infected:.3f}-{p75_peak_infected:.3f})",
            f"- Avg time to peak (days): {avg_time_to_peak_day:.3f}",
            f"- Avg attack rate (%): {avg_attack_rate_percent:.2f}",
            f"- Avg outbreak duration (days): {avg_outbreak_duration_days:.3f}",
            f"- Major outbreak probability (%): {major_outbreak_probability_percent:.2f}",
            f"- Avg infection burden AUC: {avg_infection_burden_auc:.3f}",
            f"- Avg recovery efficiency: {avg_recovery_efficiency:.3f}",
            f"- Vaccine present: {bool(scenario.population_vaccinated_fraction > 0)}",
            f"- Bedridden rule enabled: {bool(scenario.bedridden)}",
            "",
            _build_variable_definitions_text(),
        ]
    )
    ax_text.text(0.0, 1.0, summary_text, va="top", fontsize=9, family="monospace")

    fig.suptitle("Batch Iteration Analysis", fontsize=14, weight="bold")
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _write_kpi_json(path: str, payload: dict[str, object]) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def run_batch(iterations: int, steps: int, output_dir: str) -> tuple[str, str]:
    if iterations <= 0:
        raise ValueError("iterations must be > 0")
    if steps <= 0:
        raise ValueError("steps must be > 0")

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    batch_dir = os.path.join(output_dir, f"batch_{stamp}")
    os.makedirs(batch_dir, exist_ok=True)

    all_rows: list[dict[str, object]] = []
    infected_by_timestep: list[list[int]] = []
    recovered_totals: list[int] = []
    infection_totals: list[int] = []
    daily_infected_series_per_iter: list[list[float]] = []
    hourly_infected_values: list[int] = []
    iteration_summaries: list[dict[str, object]] = []

    total_days_defined = (steps * scenario.hours_per_timestep) / 24.0

    for iteration_id in range(1, iterations + 1):
        disease = scenario.make_disease()
        sim = Simulation(
            scenario.num_agents,
            scenario.width,
            scenario.height,
            disease,
            population_vaccinated_fraction=scenario.population_vaccinated_fraction,
            bedridden=scenario.bedridden,
            movement_step_size=scenario.movement_step_size(),
            initial_infected_count=scenario.initial_infected_count,
        )

        for _ in range(steps):
            sim.step()

        infected_series = sim.infected_counts
        recovered_series = sim.recovered_counts
        susceptible_series = sim.susceptible_counts
        new_infections = _compute_new_infections(infected_series)

        infection_totals.append(scenario.num_agents - susceptible_series[-1])
        recovered_totals.append(recovered_series[-1])
        infected_by_timestep.append(infected_series)
        hourly_infected_values.extend(infected_series)

        # Aggregate into day buckets for this iteration.
        day_buckets: dict[int, list[int]] = {}
        day_new_buckets: dict[int, list[int]] = {}
        for timestep_idx, infected_now in enumerate(infected_series, start=1):
            simulation_hour = timestep_idx * scenario.hours_per_timestep
            simulation_day = int((simulation_hour - 1e-9) // 24) + 1
            day_buckets.setdefault(simulation_day, []).append(infected_now)
            day_new_buckets.setdefault(simulation_day, []).append(new_infections[timestep_idx - 1])

            all_rows.append(
                {
                    "iteration_id": iteration_id,
                    "timestep_index": timestep_idx,
                    "simulation_hour": round(simulation_hour, 3),
                    "simulation_day": simulation_day,
                    "susceptible_count": susceptible_series[timestep_idx - 1],
                    "infected_count": infected_now,
                    "recovered_count": recovered_series[timestep_idx - 1],
                    "new_infections_this_step": new_infections[timestep_idx - 1],
                    "vaccine_present": bool(scenario.population_vaccinated_fraction > 0),
                    "bedridden_rule_enabled": bool(scenario.bedridden),
                }
            )

        max_day = max(day_buckets.keys()) if day_buckets else 0
        daily_avg_for_iteration = []
        for day in range(1, max_day + 1):
            infected_day_mean = _safe_mean(day_buckets.get(day, []))
            daily_avg_for_iteration.append(infected_day_mean)
        daily_infected_series_per_iter.append(daily_avg_for_iteration)

        peak_infected = max(infected_series) if infected_series else 0
        peak_step_idx = infected_series.index(peak_infected) + 1 if infected_series else 0
        time_to_peak_day = (peak_step_idx * scenario.hours_per_timestep) / 24.0 if peak_step_idx else 0.0
        attack_rate_percent = (
            ((scenario.num_agents - susceptible_series[-1]) / scenario.num_agents) * 100.0
            if scenario.num_agents
            else 0.0
        )
        non_zero_steps = sum(1 for v in infected_series if v > 0)
        outbreak_duration_days = (non_zero_steps * scenario.hours_per_timestep) / 24.0
        infection_burden_auc = sum(float(v) * scenario.hours_per_timestep for v in infected_series)
        final_infections = float(scenario.num_agents - susceptible_series[-1])
        recovery_efficiency = (recovered_series[-1] / final_infections) if final_infections > 0 else 0.0

        iteration_summaries.append(
            {
                "iteration_id": iteration_id,
                "peak_infected_count": peak_infected,
                "time_to_peak_day": round(time_to_peak_day, 6),
                "total_infected": scenario.num_agents - susceptible_series[-1],
                "total_recovered": recovered_series[-1],
                "attack_rate_percent": round(attack_rate_percent, 6),
                "outbreak_duration_days": round(outbreak_duration_days, 6),
                "infection_burden_auc": round(infection_burden_auc, 6),
                "recovery_efficiency": round(recovery_efficiency, 6),
            }
        )

        print(f"[batch] finished iteration {iteration_id}/{iterations}")

    max_steps = max(len(series) for series in infected_by_timestep)
    avg_infected_by_hour: list[float] = []
    for idx in range(max_steps):
        step_values = [series[idx] for series in infected_by_timestep if idx < len(series)]
        avg_infected_by_hour.append(_safe_mean(step_values))

    max_days = max((len(series) for series in daily_infected_series_per_iter), default=0)
    avg_infected_by_day: list[float] = []
    p25_infected_by_day: list[float] = []
    p75_infected_by_day: list[float] = []
    for day_idx in range(max_days):
        day_values = [series[day_idx] for series in daily_infected_series_per_iter if day_idx < len(series)]
        avg_infected_by_day.append(_safe_mean(day_values))
        day_values_float = [float(v) for v in day_values]
        p25_infected_by_day.append(_percentile(day_values_float, 0.25))
        p75_infected_by_day.append(_percentile(day_values_float, 0.75))

    avg_total_infections = _safe_mean([float(v) for v in infection_totals])
    avg_total_recoveries = _safe_mean([float(v) for v in recovered_totals])
    avg_infections_per_hour = _safe_mean([float(v) for v in hourly_infected_values])
    avg_infections_per_day = _safe_mean(avg_infected_by_day)

    peak_values = [float(row["peak_infected_count"]) for row in iteration_summaries]
    time_to_peak_values = [float(row["time_to_peak_day"]) for row in iteration_summaries]
    attack_rate_values = [float(row["attack_rate_percent"]) for row in iteration_summaries]
    duration_values = [float(row["outbreak_duration_days"]) for row in iteration_summaries]
    auc_values = [float(row["infection_burden_auc"]) for row in iteration_summaries]
    recovery_eff_values = [float(row["recovery_efficiency"]) for row in iteration_summaries]

    avg_peak_infected = _safe_mean(peak_values)
    p25_peak_infected = _percentile(peak_values, 0.25)
    p75_peak_infected = _percentile(peak_values, 0.75)
    avg_time_to_peak_day = _safe_mean(time_to_peak_values)
    avg_attack_rate_percent = _safe_mean(attack_rate_values)
    avg_outbreak_duration_days = _safe_mean(duration_values)
    avg_infection_burden_auc = _safe_mean(auc_values)
    avg_recovery_efficiency = _safe_mean(recovery_eff_values)
    major_outbreak_threshold_percent = 20.0
    major_outbreak_count = sum(1 for v in attack_rate_values if v >= major_outbreak_threshold_percent)
    major_outbreak_probability_percent = (major_outbreak_count / iterations) * 100.0

    aggregated_csv_path = os.path.join(batch_dir, "batch_results.csv")
    per_iteration_summary_csv_path = os.path.join(batch_dir, "batch_iteration_summary.csv")
    summary_png_path = os.path.join(batch_dir, "batch_summary.png")
    kpi_json_path = os.path.join(batch_dir, "batch_summary.json")

    _write_aggregated_csv(aggregated_csv_path, all_rows)
    _write_aggregated_csv(per_iteration_summary_csv_path, iteration_summaries)
    _write_kpi_json(
        kpi_json_path,
        {
            "iterations": iterations,
            "steps_per_iteration": steps,
            "hours_per_timestep": scenario.hours_per_timestep,
            "total_days_defined_per_iteration": total_days_defined,
            "avg_infections_per_hour": avg_infections_per_hour,
            "avg_infections_per_day": avg_infections_per_day,
            "avg_total_infections": avg_total_infections,
            "avg_total_recoveries": avg_total_recoveries,
            "avg_peak_infected": avg_peak_infected,
            "p25_peak_infected": p25_peak_infected,
            "p75_peak_infected": p75_peak_infected,
            "avg_time_to_peak_day": avg_time_to_peak_day,
            "avg_attack_rate_percent": avg_attack_rate_percent,
            "avg_outbreak_duration_days": avg_outbreak_duration_days,
            "major_outbreak_threshold_percent": major_outbreak_threshold_percent,
            "major_outbreak_probability_percent": major_outbreak_probability_percent,
            "avg_infection_burden_auc": avg_infection_burden_auc,
            "avg_recovery_efficiency": avg_recovery_efficiency,
            "vaccine_present": bool(scenario.population_vaccinated_fraction > 0),
            "bedridden_rule_enabled": bool(scenario.bedridden),
        },
    )
    _build_summary_png(
        output_path=summary_png_path,
        avg_infected_by_day=avg_infected_by_day,
        p25_infected_by_day=p25_infected_by_day,
        p75_infected_by_day=p75_infected_by_day,
        avg_total_infections=avg_total_infections,
        avg_total_recoveries=avg_total_recoveries,
        avg_infections_per_hour=avg_infections_per_hour,
        avg_infections_per_day=avg_infections_per_day,
        total_days_defined=total_days_defined,
        iterations=iterations,
        avg_peak_infected=avg_peak_infected,
        p25_peak_infected=p25_peak_infected,
        p75_peak_infected=p75_peak_infected,
        avg_time_to_peak_day=avg_time_to_peak_day,
        avg_attack_rate_percent=avg_attack_rate_percent,
        avg_outbreak_duration_days=avg_outbreak_duration_days,
        major_outbreak_probability_percent=major_outbreak_probability_percent,
        avg_infection_burden_auc=avg_infection_burden_auc,
        avg_recovery_efficiency=avg_recovery_efficiency,
    )

    print(f"[batch] wrote all iterations to: {aggregated_csv_path}")
    print(f"[batch] wrote per-iteration summary to: {per_iteration_summary_csv_path}")
    print(f"[batch] wrote summary metrics json to: {kpi_json_path}")
    print(f"[batch] wrote summary png to: {summary_png_path}")
    return aggregated_csv_path, summary_png_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run many scenario iterations and summarize outputs.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=20,
        help="Number of complete simulation iterations to run.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=scenario.timesteps,
        help="Timesteps per iteration (defaults to scenario.timesteps).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Base directory where batch artifacts are written.",
    )
    args = parser.parse_args()

    run_batch(args.iterations, args.steps, args.output_dir)


if __name__ == "__main__":
    main()
