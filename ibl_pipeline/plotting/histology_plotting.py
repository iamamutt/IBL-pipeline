import ibllib.atlas as atlas
import matplotlib.pyplot as plt
import numpy as np


def generate_spinning_brain_frames(
    trajectories, nframes_per_cycle=30, figsize=[800, 700]
):
    """
    Plots spike amps versus the time

    Parameters
    -------------
    trajectories: list of dicts
        list of dictionaries of trajectories fetched from ONE
    nframes_per_cycle: int, optional
        number of frames per cycle of spinning, default 30.
    figsize: list, [width, height], optional
        size of the images, default [800, 700]

    Return
    ------------
    frames: list of numpy.darray
        image in rgb for each frame
    """

    # libraries needed for spinning brain
    import os
    import subprocess

    from pyvirtualdisplay import Display

    # create a virtual display before importing mlab
    display = Display(visible=0, size=(1920, 1080))
    display.start()

    # mlab has to be imported after setting up the virtual display
    from atlaselectrophysiology import rendering
    from mayavi import mlab

    ba_allen = atlas.AllenAtlas(25)
    ba_needles = atlas.NeedlesAtlas(25)

    fig = rendering.figure()
    for index, trj in enumerate(trajectories):
        if trj["coordinate_system"] == "IBL-Allen":
            brain_atlas = ba_allen
        elif trj["coordinate_system"] == "Needles-Allen":
            brain_atlas = ba_needles
        else:
            brain_atlas = ba_allen
        ins = atlas.Insertion.from_dict(trj, brain_atlas=brain_atlas)
        mlapdv = brain_atlas.xyz2ccf(ins.xyz)
        if trj["provenance"] == "Ephys aligned histology track":
            color = (0, 0, 1.0)  # Blue
            mlab.plot3d(
                mlapdv[:, 1],
                mlapdv[:, 2],
                mlapdv[:, 0],
                line_width=3,
                color=color,
                tube_radius=20,
            )
    frames = []
    for i in range(nframes_per_cycle):
        mlab.view(azimuth=0, elevation=0 - i * (360 / nframes_per_cycle))
        mlab.roll(180)
        mlab.test_plot3d()
        f = mlab.gcf()
        f.scene._lift()
        frames.append(mlab.screenshot(mode="rgb", antialiased=True))

    return frames


def probe_trajectory_coronal(eid, probe_label, one, ax=None):
    """
    Generates plots of coronal sections with the channel locations

    Args:
        eid (str): session uuid (eid) for one query
        probe_label (str): probe label, e.g. probe00
        one (ONE instance): ONE instance, pre instantiated ONE instance
        ax (matplotlib.axes.Axes object, optional): Defaults to None

    Returns:
        ax (matplotlib.axes.Axes object): Axes with coronal section plotted
    """
    import brainbox.io.one as bbone

    ba_allen = atlas.AllenAtlas(25)

    one.eid2path(eid)
    traj = one.alyx.rest(
        "trajectories",
        "list",
        session=eid,
        provenance="Ephys Aligned Histology Track",
        probe=probe_label,
    )[0]
    channels = bbone.load_channel_locations(eid=eid, one=one, probe=probe_label)

    picks = one.alyx.rest("insertions", "read", id=traj["probe_insertion"])["json"]
    picks = np.array(picks["xyz_picks"]) / 1e6
    ins = atlas.Insertion.from_dict(traj)

    if ax is None:
        fig, ax = plt.subplots(1, 1, dpi=100, frameon=False)

    ax = ba_allen.plot_tilted_slice(xyz=picks, axis=1, volume="image", ax=ax)
    ax.plot(picks[:, 0] * 1e6, picks[:, 2] * 1e6)
    ax.plot(channels[probe_label]["x"] * 1e6, channels[probe_label]["z"] * 1e6, "g*")

    return ax
