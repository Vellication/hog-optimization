"""Visualize the optimal Hog strategy state space from brute_solver results."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.widgets import Slider
from scipy.ndimage import gaussian_filter

CSV_FILE = 'big_optimal_hog_strategy.csv'
INITIAL_SIGMA = 3


def load_data():
    """Load the CSV and pivot into 100x100 grids."""
    df = pd.read_csv(CSV_FILE)
    win_prob = df.pivot(index='score', columns='opponent_score', values='win_prob')
    best_roll = df.pivot(index='score', columns='opponent_score', values='best_roll')
    return df, win_prob, best_roll


def _make_mesh(grid):
    """Create X, Y meshgrid and raw Z values from a pivoted DataFrame."""
    X, Y = np.meshgrid(grid.columns.values, grid.index.values)
    Z = grid.values.astype(float)
    return X, Y, Z


def _build_surface(ax, X, Y, Z_raw, cmap, norm, zlabel, title, sigma):
    """Clear axis and draw a smoothed surface."""
    ax.clear()
    Z = gaussian_filter(Z_raw, sigma=sigma)
    colors = plt.colormaps[cmap](norm(Z))
    ax.plot_surface(X, Y, Z, facecolors=colors, rstride=1, cstride=1, shade=False)
    ax.set_xlabel('Opponent Score')
    ax.set_ylabel('Your Score')
    ax.set_zlabel(zlabel)
    ax.set_title(title)


def interactive_plot(win_prob_grid, best_roll_grid):
    """Show 3 figures each with a sigma slider for live smoothing control."""
    X_wp, Y_wp, Z_wp_raw = _make_mesh(win_prob_grid)
    X_br, Y_br, Z_br_raw = _make_mesh(best_roll_grid)
    Z_adv_raw = Z_wp_raw - 0.5

    configs = [
        {
            'X': X_wp, 'Y': Y_wp, 'Z_raw': Z_wp_raw,
            'cmap': 'RdYlGn', 'norm': plt.Normalize(0, 1),
            'zlabel': 'Win Probability',
            'title': 'Optimal Win Probability by Game State',
            'cbar_label': 'Win Probability',
        },
        {
            'X': X_br, 'Y': Y_br, 'Z_raw': Z_br_raw,
            'cmap': 'viridis', 'norm': plt.Normalize(0, 10),
            'zlabel': '# of Dice',
            'title': 'Optimal Number of Dice to Roll by Game State',
            'cbar_label': 'Optimal # of Dice',
        },
        {
            'X': X_wp, 'Y': Y_wp, 'Z_raw': Z_adv_raw,
            'cmap': 'RdBu', 'norm': plt.Normalize(-0.5, 0.5),
            'zlabel': 'Advantage',
            'title': 'Win Probability Advantage by Game State',
            'cbar_label': 'Advantage Over 50%',
        },
    ]

    figures = []
    for cfg in configs:
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_position([0.05, 0.12, 0.85, 0.82])

        _build_surface(ax, cfg['X'], cfg['Y'], cfg['Z_raw'],
                        cfg['cmap'], cfg['norm'], cfg['zlabel'],
                        cfg['title'], INITIAL_SIGMA)
        fig.colorbar(cm.ScalarMappable(norm=cfg['norm'], cmap=cfg['cmap']),
                     ax=ax, shrink=0.6, label=cfg['cbar_label'])

        slider_ax = fig.add_axes([0.25, 0.02, 0.5, 0.03])
        slider = Slider(slider_ax, 'Smoothing (σ)', 0, 10,
                        valinit=INITIAL_SIGMA, valstep=0.5)

        def make_update(a, c):
            def update(val):
                _build_surface(a, c['X'], c['Y'], c['Z_raw'],
                               c['cmap'], c['norm'], c['zlabel'],
                               c['title'], val)
                a.figure.canvas.draw_idle()
            return update

        slider.on_changed(make_update(ax, cfg))
        figures.append((fig, slider))  # prevent garbage collection

    plt.show()


if __name__ == '__main__':
    df, win_prob, best_roll = load_data()

    print(f"Loaded {len(df)} states from {CSV_FILE}")
    print(f"Overall win prob range: {df['win_prob'].min():.4f} - {df['win_prob'].max():.4f}")
    print(f"Best roll distribution:\n{df['best_roll'].value_counts().sort_index()}\n")

    interactive_plot(win_prob, best_roll)
