"""
Generate Comparison Charts for Statistical Methods
===================================================

Creates visualizations comparing the performance of different detection methods.
"""

import json
import matplotlib.pyplot as plt
import numpy as np

# Check if matplotlib is available
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib not available. Generating text-based charts only.")


def create_text_charts():
    """Create ASCII art charts for terminals without matplotlib."""

    print("="*80)
    print("STATISTICAL DETECTION METHODS - COMPARISON CHARTS (TEXT)")
    print("="*80)

    # Chart 1: Critical Test Results
    print("\n" + "="*80)
    print("Chart 1: Critical Test - 'Transitory' December 2021 Removal")
    print("="*80)

    methods = ['Kleinberg', 'G-test', 'JSD', 'Improved']
    results = ['PASS', 'FAIL', 'FAIL', 'PASS']

    print("\nMethod                    Result")
    print("-" * 40)
    for method, result in zip(methods, results):
        symbol = "✓" if result == "PASS" else "✗"
        print(f"{method:<25s} {symbol} {result}")

    # Chart 2: Performance Metrics
    print("\n" + "="*80)
    print("Chart 2: Backtest Performance Metrics")
    print("="*80)

    metrics = {
        'G-test': {'precision': 0.000, 'recall': 0.000, 'f1': 0.000},
        'JSD': {'precision': 0.000, 'recall': 0.000, 'f1': 0.000},
        'Improved': {'precision': 0.553, 'recall': 0.162, 'f1': 0.250}
    }

    print("\nMethod        Precision  Recall    F1 Score")
    print("-" * 45)
    for method, scores in metrics.items():
        print(f"{method:<12s}  {scores['precision']:>6.3f}    {scores['recall']:>6.3f}   {scores['f1']:>6.3f}")

    # Chart 3: Detection Counts
    print("\n" + "="*80)
    print("Chart 3: Total Detections by Method")
    print("="*80)

    detections = {
        'Kleinberg': 6,
        'G-test': 0,
        'JSD': 1,
        'Improved': 38
    }

    print("\nMethod        Detections  Bar Chart")
    print("-" * 50)
    for method, count in detections.items():
        bar = "█" * (count // 2) if count > 0 else ""
        print(f"{method:<12s}  {count:>6d}     {bar}")

    print("\nGround Truth Total: 130 shifts")

    # Chart 4: Confusion Matrix (Improved Hybrid)
    print("\n" + "="*80)
    print("Chart 4: Confusion Matrix - Improved Hybrid Detector")
    print("="*80)

    print("\n                    Predicted")
    print("                 Shift    No Shift")
    print("Actual  Shift      21        109     (TP=21, FN=109)")
    print("        No Shift   17         --     (FP=17)")
    print("\nPrecision: 21/(21+17) = 0.553")
    print("Recall:    21/(21+109) = 0.162")

    # Chart 5: Execution Time
    print("\n" + "="*80)
    print("Chart 5: Execution Time (seconds)")
    print("="*80)

    times = {
        'Kleinberg': 1.32,
        'G-test': 0.82,
        'JSD': 0.91,
        'Improved': 0.95
    }

    print("\nMethod        Time (s)   Bar Chart")
    print("-" * 50)
    for method, time_val in times.items():
        bar = "▓" * int(time_val * 30)
        print(f"{method:<12s}  {time_val:>6.2f}    {bar}")

    print("\nAll methods fast enough for real-time use (<2 seconds)")


def create_visual_charts():
    """Create matplotlib charts if available."""

    if not MATPLOTLIB_AVAILABLE:
        print("\nMatplotlib not available. Skipping visual charts.")
        return

    print("\n" + "="*80)
    print("Generating matplotlib charts...")
    print("="*80)

    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Statistical Detection Methods - Performance Comparison',
                 fontsize=16, fontweight='bold')

    # Chart 1: Critical Test Results
    ax1 = axes[0, 0]
    methods = ['Kleinberg', 'G-test', 'JSD', 'Improved\nHybrid']
    results = [1, 0, 0, 1]  # 1 = PASS, 0 = FAIL
    colors = ['green' if r == 1 else 'red' for r in results]

    bars = ax1.bar(methods, results, color=colors, alpha=0.7, edgecolor='black')
    ax1.set_ylabel('Result (1=Pass, 0=Fail)', fontweight='bold')
    ax1.set_title('Critical Test: Transitory Dec 2021 Removal', fontweight='bold')
    ax1.set_ylim([0, 1.2])
    ax1.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)

    for bar, result in zip(bars, results):
        height = bar.get_height()
        label = 'PASS' if result == 1 else 'FAIL'
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                label, ha='center', va='bottom', fontweight='bold')

    # Chart 2: Performance Metrics
    ax2 = axes[0, 1]
    methods_perf = ['G-test', 'JSD', 'Improved\nHybrid']
    precision = [0.000, 0.000, 0.553]
    recall = [0.000, 0.000, 0.162]
    f1 = [0.000, 0.000, 0.250]

    x = np.arange(len(methods_perf))
    width = 0.25

    ax2.bar(x - width, precision, width, label='Precision', alpha=0.8, color='blue')
    ax2.bar(x, recall, width, label='Recall', alpha=0.8, color='orange')
    ax2.bar(x + width, f1, width, label='F1 Score', alpha=0.8, color='green')

    ax2.set_ylabel('Score', fontweight='bold')
    ax2.set_title('Backtest Performance Metrics', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(methods_perf)
    ax2.legend()
    ax2.set_ylim([0, 0.7])

    # Chart 3: Detection Counts
    ax3 = axes[1, 0]
    methods_det = ['Kleinberg', 'G-test', 'JSD', 'Improved\nHybrid']
    detections = [6, 0, 1, 38]

    bars = ax3.barh(methods_det, detections, alpha=0.7, color='steelblue', edgecolor='black')
    ax3.set_xlabel('Number of Detections', fontweight='bold')
    ax3.set_title('Total Detections by Method', fontweight='bold')
    ax3.axvline(x=130, color='red', linestyle='--', linewidth=2, label='Ground Truth (130)')
    ax3.legend()

    for bar, count in zip(bars, detections):
        width_val = bar.get_width()
        ax3.text(width_val + 2, bar.get_y() + bar.get_height()/2.,
                f'{count}', ha='left', va='center', fontweight='bold')

    # Chart 4: Precision-Recall Trade-off
    ax4 = axes[1, 1]

    # Plot precision vs recall for improved method
    # Show the trade-off space
    ax4.scatter([0.162], [0.553], s=200, c='green', marker='o',
               edgecolors='black', linewidths=2, label='Improved Hybrid', zorder=3)

    # Show failed methods at origin
    ax4.scatter([0.000, 0.000], [0.000, 0.000], s=100, c='red', marker='x',
               linewidths=2, label='G-test & JSD', zorder=2)

    # Draw F1 contours
    recall_range = np.linspace(0.01, 1, 100)
    for f1_val in [0.1, 0.2, 0.3, 0.4, 0.5]:
        precision_curve = (f1_val * recall_range) / (2 * recall_range - f1_val)
        precision_curve = np.clip(precision_curve, 0, 1)
        ax4.plot(recall_range, precision_curve, 'gray', alpha=0.3, linestyle='--')
        # Label F1 curves
        if f1_val in [0.2, 0.3, 0.4]:
            ax4.text(0.9, precision_curve[-10], f'F1={f1_val}',
                    fontsize=8, color='gray', alpha=0.7)

    ax4.set_xlabel('Recall', fontweight='bold')
    ax4.set_ylabel('Precision', fontweight='bold')
    ax4.set_title('Precision-Recall Trade-off', fontweight='bold')
    ax4.set_xlim([0, 1])
    ax4.set_ylim([0, 1])
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save figure
    output_file = '/mnt/c/python/FedSpeak/prototypes/results/method_comparison_charts.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Charts saved to: {output_file}")

    plt.close()


if __name__ == "__main__":
    # Always create text charts
    create_text_charts()

    # Try to create visual charts
    create_visual_charts()

    print("\n" + "="*80)
    print("Chart generation complete!")
    print("="*80)
