import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle
import numpy as np

# Створюємо фігуру 512x512
fig, ax = plt.subplots(1, 1, figsize=(5.12, 5.12), dpi=100)
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_aspect('equal')

# Градієнтний фон (імітація)
colors = ['#FF6B35', '#F7931E', '#FFD23F']  # помаранчевий градієнт
for i, color in enumerate(colors):
    circle = Circle((5, 5), 5-i*0.8, color=color, alpha=0.3)
    ax.add_patch(circle)

# Основне коло
main_circle = Circle((5, 5), 4, color='#FF6B35', alpha=0.9)
ax.add_patch(main_circle)

# Додаємо літеру "M"
ax.text(5, 5, 'M', fontsize=120, ha='center', va='center', 
        color='white', weight='bold', family='Arial')

# Додаємо маленький текст
ax.text(5, 2, 'Diet', fontsize=20, ha='center', va='center', 
        color='white', weight='bold', family='Arial')

# Прибираємо осі
ax.set_xticks([])
ax.set_yticks([])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

# Зберігаємо
plt.tight_layout()
plt.savefig('mydiet_logo.png', dpi=100, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
plt.close()

print("Логотип створено: mydiet_logo.png")
print("Розмір: 512x512 пікселів")
print("Готовий для використання в BotFather!")