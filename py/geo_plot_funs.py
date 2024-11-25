import sys
sys.path.append('py')
from features_funs import *
from matplotlib.lines import Line2D
import contextily as cx
import matplotlib.pyplot as plt
from cartopy import crs as ccrs

def plot_group(df,
               colors=None,
               marker_size=0.1,
               fig_size=(10, 10),
               show_legend=False
               ):
    if colors is None:
        cmap = plt.cm.Set1
        unique_groups = df['group'].unique()
        colors = {group: cmap(i / len(unique_groups))
                  for i, group
                  in enumerate(unique_groups)
                  }

    # plot setup
    fig, ax = plt.subplots(figsize=fig_size)

    # groups plotting
    for group, color in colors.items():
        (
            df[df['group'] == group]
            .to_crs('EPSG:3857')
            .plot(ax=ax,
                  color=color,
                  label=group,
                  markersize=marker_size
                  )
        )

    # map img
    cx.add_basemap(ax)

    # legend
    legend_elements = [Line2D([0],
                              [0],
                              marker='o',
                              color='w',
                              markerfacecolor=color,
                              markersize=10,
                              label=group
                              )
                       for group, color
                       in colors.items()
                       ]

    if show_legend:
        ax.legend(handles=legend_elements,
                  loc="upper right",
                  ncol=3,
                  fontsize=8
                  )

    # Remove both ticks and labels
    ax.set_xticks([])
    ax.set_yticks([])

    # final show
    plt.show()


def filter_df(df, group_list):
    return df[df['group'].isin(group_list)]


def get_group_with_pattern(df, pattern):
    return df[df['group'].str.contains(pattern)]['group'].unique()