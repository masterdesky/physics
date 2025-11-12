from spacepy.pybats.bats import Bats2d
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

# Path to a downloaded Z=0 cut-plane file from Nomads
filename = 'z0_20251110T2030_20251111T002300'  # adjust to your file
# Read the file; Bats2d auto‑detects endian-ness
data = Bats2d(filename)

# Extract coordinates (in Earth radii, Re) and pressure (nPa)
x = data['x']  # X coordinates
y = data['y']  # Y coordinates
p = data['p']  # plasma pressure (nPa)

# The data are unstructured (1-D), so use triangular interpolation for plotting
tri = mtri.Triangulation(x, y)

# Create plot
fig, ax = plt.subplots(figsize=(8, 4))
tcf = ax.tricontourf(tri, p, levels=128, cmap='RdYlBu_r')

# Add colorbar and labels
cb = fig.colorbar(tcf, ax=ax, label='Pressure (nPa)')
ax.set_aspect('equal')
ax.set_xlabel('X (Re)')
ax.set_ylabel('Y (Re)')
ax.set_title(f'Geospace Magnetosphere Cut Plane Pressure\n{data.attrs.get('time', 'Unknown Time')}')

plt.show()
