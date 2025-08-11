import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch, Arrow
import matplotlib.lines as mlines

# Create figure and axis
fig, ax = plt.subplots(1, 1, figsize=(12, 10))
ax.set_xlim(-6, 6)
ax.set_ylim(-6, 6)
ax.set_aspect('equal')

# Draw outer pressure vessel (sphere in 2D cross-section)
outer_sphere = Circle((0, 0), 5, fill=False, edgecolor='black', linewidth=3)
ax.add_patch(outer_sphere)

# Draw inner core region
core_sphere = Circle((0, 0), 3, fill=True, facecolor='#FFE4B5', edgecolor='darkred', linewidth=2, alpha=0.7)
ax.add_patch(core_sphere)

# Draw fuel assemblies in the core
fuel_positions = [
    (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),
    (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7),
    (1.5, 0.5), (-1.5, 0.5), (1.5, -0.5), (-1.5, -0.5)
]
for pos in fuel_positions:
    fuel = Circle(pos, 0.3, fill=True, facecolor='#FF6B6B', edgecolor='darkred', linewidth=1)
    ax.add_patch(fuel)

# Draw control rods (vertical)
control_rod_positions = [(0, 3.5), (1.5, 3.5), (-1.5, 3.5)]
for x_pos, y_pos in control_rod_positions:
    # Rod housing
    rod_housing = Rectangle((x_pos - 0.2, y_pos - 1), 0.4, 2, 
                           fill=True, facecolor='gray', edgecolor='black')
    ax.add_patch(rod_housing)
    
    # Control rod (partially inserted)
    control_rod = Rectangle((x_pos - 0.15, y_pos - 0.8), 0.3, 1.5, 
                           fill=True, facecolor='#4A4A4A', edgecolor='black')
    ax.add_patch(control_rod)
    
    # Arrow showing movement capability
    ax.annotate('', xy=(x_pos, y_pos + 0.3), xytext=(x_pos, y_pos + 0.8),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))

# Draw water coolant flow (curved arrows)
# Inlet
ax.annotate('', xy=(-3.5, -3.5), xytext=(-4.5, -4.5),
            arrowprops=dict(arrowstyle='->', color='blue', lw=3))
ax.text(-5, -4.8, 'Cool Water In', color='blue', fontsize=10, weight='bold')

# Outlet
ax.annotate('', xy=(4.5, -4.5), xytext=(3.5, -3.5),
            arrowprops=dict(arrowstyle='->', color='red', lw=3))
ax.text(4.2, -4.8, 'Hot Water Out', color='red', fontsize=10, weight='bold')

# Draw water flow patterns inside
theta = np.linspace(0, 2*np.pi, 8, endpoint=False)
for i, t in enumerate(theta[::2]):
    x_start = 3.5 * np.cos(t)
    y_start = 3.5 * np.sin(t)
    x_end = 4.5 * np.cos(t)
    y_end = 4.5 * np.sin(t)
    
    # Water flow lines
    ax.plot([x_start, x_end], [y_start, y_end], 'b--', alpha=0.5, linewidth=1)

# Add neutron visualization (small dots representing neutrons)
np.random.seed(42)
n_neutrons = 30
neutron_r = 2.5 * np.sqrt(np.random.random(n_neutrons))
neutron_theta = 2 * np.pi * np.random.random(n_neutrons)
neutron_x = neutron_r * np.cos(neutron_theta)
neutron_y = neutron_r * np.sin(neutron_theta)

for i in range(n_neutrons):
    neutron = Circle((neutron_x[i], neutron_y[i]), 0.08, 
                    fill=True, facecolor='green', alpha=0.7)
    ax.add_patch(neutron)

# Add labels and annotations
ax.text(0, -5.5, 'Spherical Water Nuclear Fission Reactor', 
        fontsize=16, weight='bold', ha='center')
ax.text(0, -6, '(Simplified Cross-Section View)', 
        fontsize=12, ha='center', style='italic')

# Component labels
ax.text(0, 2, 'Fissile Core', fontsize=10, ha='center', 
        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.5))
ax.text(0, 4.5, 'Control Rods', fontsize=10, ha='center')
ax.text(-3.5, 0, 'Water\nModerator/\nCoolant', fontsize=9, ha='center', color='blue')

# Add legend
fuel_patch = patches.Circle((0, 0), 0.1, facecolor='#FF6B6B', edgecolor='darkred')
control_patch = patches.Rectangle((0, 0), 0.2, 0.2, facecolor='#4A4A4A')
neutron_patch = patches.Circle((0, 0), 0.1, facecolor='green', alpha=0.7)
water_line = mlines.Line2D([0], [0], color='blue', linewidth=2, linestyle='--')

ax.legend([fuel_patch, control_patch, neutron_patch, water_line],
          ['Fuel Assembly', 'Control Rod', 'Neutron', 'Water Flow'],
          loc='upper right', bbox_to_anchor=(1.15, 1))

# Add reactor physics annotations
ax.text(5.5, 3, 'k-eff < 1.0\n(Subcritical)', fontsize=9, 
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.5))
ax.text(5.5, 2, 'Neutron Population:\nDecreasing', fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.5))

# Remove axis
ax.set_xticks([])
ax.set_yticks([])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

plt.tight_layout()
plt.savefig('spherical_reactor_design.png', dpi=300, bbox_inches='tight')
plt.show()