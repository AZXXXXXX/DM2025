import os
from pathlib import Path
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager

matplotlib.use('Agg')


def get_font_path() -> str:
    current_dir = Path(__file__).parent.parent
    font_path = current_dir / "fonts" / "simhei.ttf"
    return str(font_path)


def configure_matplotlib_chinese() -> None:
    font_path = get_font_path()
    
    if not os.path.exists(font_path):
        print(f"Warning: Chinese font not found at {font_path}")
        return
    
    font_manager.fontManager.addfont(font_path)
    
    font_prop = font_manager.FontProperties(fname=font_path)
    font_name = font_prop.get_name()
    
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
    plt.rcParams['axes.unicode_minus'] = False


def get_font_properties() -> font_manager.FontProperties:
    font_path = get_font_path()
    if os.path.exists(font_path):
        return font_manager.FontProperties(fname=font_path)
    return font_manager.FontProperties()


try:
    configure_matplotlib_chinese()
except Exception:
    pass
