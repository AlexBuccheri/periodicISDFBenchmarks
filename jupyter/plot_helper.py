from collections.abc import Mapping, Sequence
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from pandas import DataFrame


def _normalise_datasets(
    data: DataFrame | Mapping[str, DataFrame] | Sequence[DataFrame],
    dataset_names: Optional[Sequence[str]] = None,
) -> list[tuple[Optional[str], DataFrame]]:
    if isinstance(data, DataFrame):
        return [(None, data)]

    if isinstance(data, Mapping):
        return list(data.items())

    if dataset_names is None:
        dataset_names = [f"set {idx + 1}" for idx in range(len(data))]

    if len(dataset_names) != len(data):
        raise ValueError("dataset_names must match the number of datasets")

    return list(zip(dataset_names, data))


def _plot_columns(y_axis: str) -> tuple[str, str, str]:
    if y_axis == "time":
        return "SELF TOTAL_TIME", "SELF %TIME", "Time (s)"

    if y_axis == "percent":
        return "SELF %TIME", "SELF TOTAL_TIME", "Self time (%)"

    raise ValueError("y_axis must be either 'time' or 'percent'")


def _format_bar_label(column: str, value: float) -> str:
    if column.endswith("%TIME"):
        return f"{value:.1f}%"

    return f"{value:.3f} s"


def barplot_self_times(
    data: DataFrame | Mapping[str, DataFrame] | Sequence[DataFrame],
    labels: Sequence[str],
    fig_ax: Optional[tuple] = None,
    dataset_names: Optional[Sequence[str]] = None,
    y_axis: str = "time",
):
    """

    :param data:
    :param labels:
    :param fig_ax:
    :param dataset_names:
    :param y_axis: "time" or "percent"
    :return:
    """
    if fig_ax is None:
        fig, ax = plt.subplots(figsize=(9, 4.5))
    else:
        fig, ax = fig_ax

    datasets = _normalise_datasets(data, dataset_names)
    value_col, label_col, ylabel = _plot_columns(y_axis)
    x_positions = list(range(len(labels)))
    num_datasets = len(datasets)
    width = 0.8 / max(num_datasets, 1)
    max_value = 0.0

    for idx, (name, df) in enumerate(datasets):
        plot_df = df.loc[labels, [value_col, label_col]]
        max_value = max(max_value, float(plot_df[value_col].max()))

        if num_datasets == 1:
            bar_positions = x_positions
            color = "steelblue"
        else:
            offset = (idx - (num_datasets - 1) / 2) * width
            bar_positions = [x + offset for x in x_positions]
            color = None

        bars = ax.bar(
            bar_positions,
            plot_df[value_col],
            width=width,
            color=color,
            label=name,
        )

        for bar, value in zip(bars, plot_df[label_col]):
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height()
            ax.text(x, y, _format_bar_label(label_col, value), ha="center", va="bottom")

    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.set_xticks(x_positions, labels)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    if max_value > 0:
        ax.set_ylim(0, max_value * 1.15)

    if num_datasets > 1:
        ax.legend()

    return fig, ax


def cumulative_and_self(df: DataFrame, labels, fig_ax: Optional[tuple] = None):

    plot_df = df.loc[labels, [
        "CUM TOTAL_TIME",
        "CUM %TIME",
        "SELF TOTAL_TIME",
        "SELF %TIME",
    ]].copy()

    plot_df = plot_df.sort_values("CUM TOTAL_TIME", ascending=False)

    if fig_ax is None:
        fig, ax = plt.subplots(figsize=(9, 4.5))
    else:
        fig, ax = fig_ax

    x = np.arange(len(plot_df))
    width = 0.38

    bars_cum = ax.bar(
        x - width / 2,
        plot_df["CUM TOTAL_TIME"],
        width,
        label="Cumulative",
    )

    _ = ax.bar(
        x + width / 2,
        plot_df["SELF TOTAL_TIME"],
        width,
        label="Self",
    )

    ax.set_ylabel("Time (s)")
    ax.set_xlabel("")
    ax.set_title("Cumulative vs self time")
    ax.set_xticks(x)
    ax.set_xticklabels(plot_df.index, rotation=45, ha="right")
    ax.legend()

    for bar, pct in zip(bars_cum, plot_df["CUM %TIME"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{pct:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    return fig, ax