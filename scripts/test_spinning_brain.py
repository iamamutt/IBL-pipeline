import subprocess

subprocess.Popen(["Xvfb", ":1", "-screen", "0", "1280x1024x24", "-auth", "localhost"])

"""
Generates 3D rendering of all probe trajectories for a single subject.
The trajectory plotted are:
'Micro-manipulator': Green
'Histology track': Red
'Planned': Blue
"""
import ibllib.atlas as atlas
import imageio
from atlaselectrophysiology import rendering

# Author: Olivier
# environment installation guide https://github.com/int-brain-lab/iblenv
# run "%qui qt" magic command from Ipython prompt for interactive mode
from mayavi import mlab
from oneibl.one import ONE

# GIF export params
file_name = "animation.gif"
fps = 20

# Code to generate figure
one = ONE(base_url="https://alyx.internationalbrainlab.org")

fig = rendering.figure()

subject = "KS003"
trajs = one.alyx.rest("trajectories", "list", subject=subject)

ba_allen = atlas.AllenAtlas(25)
ba_needles = atlas.NeedlesAtlas(25)

plt_trj = []

for index, trj in enumerate(trajs):
    if trj["coordinate_system"] == "IBL-Allen":
        brain_atlas = ba_allen
    elif trj["coordinate_system"] == "Needles-Allen":
        brain_atlas = ba_needles
    ins = atlas.Insertion.from_dict(trj, brain_atlas=brain_atlas)
    ins = atlas.Insertion.from_dict(trj, brain_atlas=ba_allen)

    mlapdv = brain_atlas.xyz2ccf(ins.xyz)
    if trj["provenance"] == "Micro-manipulator":
        color = (0.0, 1.0, 0.0)  # Green
    elif trj["provenance"] == "Histology track":
        color = (1.0, 0.0, 0.0)  # Red
    elif trj["provenance"] == "Planned":
        color = (0.0, 0.0, 1.0)  # Blue

    lab = (
        f"{trj['session']['subject']}/{trj['session']['start_time'][:10]}"
        + f"{str(trj['session']['number']).zfill(3)}"
    )
    plt = mlab.plot3d(
        mlapdv[:, 1],
        mlapdv[:, 2],
        mlapdv[:, 0],
        line_width=3,
        color=color,
        tube_radius=20,
    )
    # setup the labels at the top of the trajectories
    mlab.text3d(
        mlapdv[0, 1],
        mlapdv[0, 2],
        mlapdv[0, 0] - 500,
        lab,
        line_width=4,
        color=tuple(color),
        figure=fig,
        scale=150,
    )
    plt_trj.append(plt)


frames = []

for i in range(fps):
    mlab.view(azimuth=0, elevation=0 - i * (360 / fps))
    mlab.roll(180)
    mlab.test_plot3d()
    f = mlab.gcf()
    f.scene._lift()
    frames.append(mlab.screenshot(mode="rgb", antialiased=True))

imageio.mimsave(file_name, frames, duration=(1 / fps))
