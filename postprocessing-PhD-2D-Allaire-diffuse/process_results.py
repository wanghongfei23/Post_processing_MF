#!/usr/bin/env python3
"""
后处理脚本 - 用于处理 Allaire 扩散模型的结果文件

使用方法：
1. 将 output 文件夹中的 .dat 文件复制到 postprocessing/results 文件夹
2. 运行：python process_results.py

生成的文件将保存在 postprocessing/plots 文件夹中
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import glob
from datetime import datetime
import imageio.v2 as imageio

# 结果文件夹路径
RESULTS_DIR = 'results'
# 输出图像文件夹
PLOTS_DIR = 'plots'

# 算例配置字典 - 存储不同算例的参数
CASE_CONFIGS = {
    'RMI_SF6': {
        'default_resolution': (1000, 200),
        'figure_size': (12, 4),
        'description': ' Richtmyer-Meshkov Instability with SF6'
    },
    'tin_air_implosion': {
        'default_resolution': (800, 1600),  # 根据settingsfile.txt设置的实际分辨率
        'figure_size': (8, 16),  # 匹配分辨率比例的图像大小
        'description': 'Tin-Air Implosion'
    },
    # 可以添加其他算例的配置
    'DEFAULT': {
        'default_resolution': (1000, 200),
        'figure_size': (12, 4),
        'description': 'Default configuration'
    }
}

# 确保输出文件夹存在
os.makedirs(PLOTS_DIR, exist_ok=True)

def get_case_config(filename):
    """从文件名中提取算例名称并返回相应的配置"""
    # 从文件名中提取算例名称（文件名格式: CASE_NAME-MUSCL-Nx-Ny-state-time.dat）
    parts = filename.split('-')
    if len(parts) > 0:
        case_name = parts[0]
        if case_name in CASE_CONFIGS:
            return case_name, CASE_CONFIGS[case_name]
    # 如果未找到匹配的算例，使用默认配置
    return 'DEFAULT', CASE_CONFIGS['DEFAULT']

def process_state_files():
    """处理 state 文件"""
    state_files = glob.glob(os.path.join(RESULTS_DIR, '*state*.dat'))
    if not state_files:
        print("未找到 state 文件")
        return
    
    # 按时间值排序文件
    def get_time_from_filename(file_path):
        filename = os.path.basename(file_path)
        time_str = filename.split('-state-')[1].replace('.dat', '')
        return float(time_str)
    
    state_files = sorted(state_files, key=get_time_from_filename)
    
    print(f"找到 {len(state_files)} 个 state 文件")
    
    for file_path in state_files:
        filename = os.path.basename(file_path)
        time_str = filename.split('-state-')[1].replace('.dat', '')
        time = float(time_str)
        
        # 获取算例配置
        case_name, config = get_case_config(filename)
        default_resolution = config['default_resolution']
        figure_size = config['figure_size']
        
        # 读取数据
        data = np.loadtxt(file_path)
        x = data[:, 0]
        y = data[:, 1]
        rho = data[:, 2]  # 密度
        z = data[:, 6]     # 体积分数
        p = data[:, 7]     # 压力
        
        # 尝试从文件名中提取分辨率信息
        # 文件名格式：CASE_NAME-MUSCL-100-100-state-0.000000.dat
        parts = filename.split('-')
        Nx, Ny = None, None
        if len(parts) >= 4:
            try:
                Nx = int(parts[2])
                Ny = int(parts[3])
            except ValueError:
                # 如果无法从文件名提取分辨率，将从数据中推断
                pass
        
        # 如果无法从文件名获取分辨率，从数据中推断
        if Nx is None or Ny is None:
            # 数据点数量
            num_points = len(data)
            # 尝试不同的分辨率组合，找到能整除的
            # 首先尝试默认分辨率
            if num_points == default_resolution[0] * default_resolution[1]:
                Nx, Ny = default_resolution
            else:
                # 尝试其他可能的分辨率
                # 这里简单处理，实际应用中可能需要更复杂的逻辑
                # 假设 Nx 和 Ny 的比例与默认分辨率相同
                aspect_ratio = default_resolution[1] / default_resolution[0]
                # 计算可能的 Nx
                Nx = int((num_points / aspect_ratio) ** 0.5)
                Ny = int(num_points / Nx)
                # 调整以确保 Nx * Ny = num_points
                while Nx * Ny != num_points and Nx > 0:
                    Nx += 1
                    Ny = int(num_points / Nx)
                if Nx * Ny != num_points:
                    # 如果仍然无法找到合适的分辨率，使用默认值
                    Nx, Ny = default_resolution
                    print(f"警告：无法从数据中推断分辨率，使用默认值 {Nx}x{Ny}")
                else:
                    print(f"从数据中推断分辨率：{Nx}x{Ny}")
        
        # 重塑为二维网格
        X = x.reshape(Ny, Nx)
        Y = y.reshape(Ny, Nx)
        RHO = rho.reshape(Ny, Nx)
        Z = z.reshape(Ny, Nx)
        P = p.reshape(Ny, Nx)
        
        # 计算适合的图像尺寸，基于实际计算域大小
        # 从数据中获取计算域的实际范围
        x_min, x_max = np.min(x), np.max(x)
        y_min, y_max = np.min(y), np.max(y)
        # 计算计算域的宽高比
        domain_width = x_max - x_min
        domain_height = y_max - y_min
        aspect_ratio = domain_width / domain_height
        # 设定基础高度，然后根据宽高比计算宽度
        base_height = 6
        calculated_width = base_height * aspect_ratio
        # 确保宽度和高度在合理范围内
        calculated_width = max(8, min(calculated_width, 16))
        base_height = max(4, min(base_height, 12))
        
        # 绘制密度场 - 提高精度到 6 位小数
        plt.figure(figsize=(calculated_width, base_height))
        plt.contourf(X, Y, RHO, levels=50, cmap='jet')
        plt.colorbar(label='Density')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(f'Density Field at t={time:.6f} ({case_name})')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'density_{time:.6f}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 绘制体积分数（界面位置）- 提高精度到 6 位小数
        plt.figure(figsize=(calculated_width, base_height))
        plt.contourf(X, Y, Z, levels=50, cmap='coolwarm')
        plt.colorbar(label='Volume Fraction')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(f'Interface Location at t={time:.6f} ({case_name})')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'interface_{time:.6f}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 绘制压力场 - 提高精度到 6 位小数
        plt.figure(figsize=(calculated_width, base_height))
        plt.contourf(X, Y, P, levels=50, cmap='viridis')
        plt.colorbar(label='Pressure')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(f'Pressure Field at t={time:.6f} ({case_name})')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'pressure_{time:.6f}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"处理完成：{filename} (算例：{case_name})")

def process_schlieren_files():
    """处理 schlieren 文件"""
    schlieren_files = glob.glob(os.path.join(RESULTS_DIR, '*schlieren*.dat'))
    if not schlieren_files:
        print("未找到 schlieren 文件")
        return
    
    # 按时间值排序文件
    def get_time_from_filename(file_path):
        filename = os.path.basename(file_path)
        time_str = filename.split('-schlieren-')[1].replace('.dat', '')
        return float(time_str)
    
    schlieren_files = sorted(schlieren_files, key=get_time_from_filename)
    
    print(f"找到 {len(schlieren_files)} 个 schlieren 文件")
    
    for file_path in schlieren_files:
        filename = os.path.basename(file_path)
        time_str = filename.split('-schlieren-')[1].replace('.dat', '')
        time = float(time_str)
        
        # 获取算例配置
        case_name, config = get_case_config(filename)
        default_resolution = config['default_resolution']
        figure_size = config['figure_size']
        
        # 读取数据
        data = np.loadtxt(file_path)
        x = data[:, 0]
        y = data[:, 1]
        grad = data[:, 2]  # 归一化密度梯度
        
        # 尝试从文件名中提取分辨率信息
        # 文件名格式: CASE_NAME-MUSCL-100-100-schlieren-0.000000.dat
        parts = filename.split('-')
        Nx, Ny = None, None
        if len(parts) >= 4:
            try:
                Nx = int(parts[2])
                Ny = int(parts[3])
            except ValueError:
                # 如果无法从文件名提取分辨率，将从数据中推断
                pass
        
        # 如果无法从文件名获取分辨率，从数据中推断
        if Nx is None or Ny is None:
            # 数据点数量
            num_points = len(data)
            # 尝试不同的分辨率组合，找到能整除的
            # 首先尝试默认分辨率
            if num_points == default_resolution[0] * default_resolution[1]:
                Nx, Ny = default_resolution
            else:
                # 尝试其他可能的分辨率
                # 这里简单处理，实际应用中可能需要更复杂的逻辑
                # 假设 Nx 和 Ny 的比例与默认分辨率相同
                aspect_ratio = default_resolution[1] / default_resolution[0]
                # 计算可能的 Nx
                Nx = int((num_points / aspect_ratio) ** 0.5)
                Ny = int(num_points / Nx)
                # 调整以确保 Nx * Ny = num_points
                while Nx * Ny != num_points and Nx > 0:
                    Nx += 1
                    Ny = int(num_points / Nx)
                if Nx * Ny != num_points:
                    # 如果仍然无法找到合适的分辨率，使用默认值
                    Nx, Ny = default_resolution
                    print(f"警告：无法从数据中推断分辨率，使用默认值 {Nx}x{Ny}")
                else:
                    print(f"从数据中推断分辨率：{Nx}x{Ny}")
        
        # 重塑为二维网格
        X = x.reshape(Ny, Nx)
        Y = y.reshape(Ny, Nx)
        GRAD = grad.reshape(Ny, Nx)
        
        # 计算适合的图像尺寸，基于实际计算域大小
        # 从数据中获取计算域的实际范围
        x_min, x_max = np.min(x), np.max(x)
        y_min, y_max = np.min(y), np.max(y)
        # 计算计算域的宽高比
        domain_width = x_max - x_min
        domain_height = y_max - y_min
        aspect_ratio = domain_width / domain_height
        # 设定基础高度，然后根据宽高比计算宽度
        base_height = 6
        calculated_width = base_height * aspect_ratio
        # 确保宽度和高度在合理范围内
        calculated_width = max(8, min(calculated_width, 16))
        base_height = max(4, min(base_height, 12))
        
        # 绘制纹影图 - 提高精度到 6 位小数
        plt.figure(figsize=(calculated_width, base_height))
        plt.contourf(X, Y, GRAD, levels=50, cmap='gray')
        plt.colorbar(label='Normalized Density Gradient')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(f'Schlieren Image at t={time:.6f} ({case_name})')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'schlieren_{time:.6f}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"处理完成：{filename} (算例：{case_name})")

def process_lineout_files():
    """处理 lineout 文件"""
    lineoutx_files = sorted(glob.glob(os.path.join(RESULTS_DIR, '*lineoutx*.dat')))
    lineouty_files = sorted(glob.glob(os.path.join(RESULTS_DIR, '*lineouty*.dat')))
    
    if not lineoutx_files and not lineouty_files:
        print("未找到 lineout 文件")
        return
    
    print(f"找到 {len(lineoutx_files)} 个 lineoutx 文件")
    print(f"找到 {len(lineouty_files)} 个 lineouty 文件")
    
    # 处理 x 方向 lineout
    for file_path in lineoutx_files:
        filename = os.path.basename(file_path)
        step = filename.split('-lineoutx-')[1].replace('.dat', '')
        
        # 获取算例配置
        case_name, config = get_case_config(filename)
        
        # 读取数据
        data = np.loadtxt(file_path)
        x = data[:, 0]
        rho = data[:, 1]
        u = data[:, 2]
        v = data[:, 3]
        e = data[:, 4]
        z = data[:, 5]
        p = data[:, 6]
        
        # 绘制多个物理量
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        plt.plot(x, rho)
        plt.xlabel('x')
        plt.ylabel('Density')
        plt.title(f'Density (Step {step}) ({case_name})')
        
        plt.subplot(2, 2, 2)
        plt.plot(x, p)
        plt.xlabel('x')
        plt.ylabel('Pressure')
        plt.title(f'Pressure (Step {step}) ({case_name})')
        
        plt.subplot(2, 2, 3)
        plt.plot(x, z)
        plt.xlabel('x')
        plt.ylabel('Volume Fraction')
        plt.title(f'Volume Fraction (Step {step}) ({case_name})')
        
        plt.subplot(2, 2, 4)
        plt.plot(x, u, label='u')
        plt.plot(x, v, label='v')
        plt.xlabel('x')
        plt.ylabel('Velocity')
        plt.title(f'Velocity Components (Step {step}) ({case_name})')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'lineoutx_{step}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"处理完成：{filename} (算例：{case_name})")
    
    # 处理 y 方向 lineout
    for file_path in lineouty_files:
        filename = os.path.basename(file_path)
        step = filename.split('-lineouty-')[1].replace('.dat', '')
        
        # 获取算例配置
        case_name, config = get_case_config(filename)
        
        # 读取数据
        data = np.loadtxt(file_path)
        y = data[:, 0]
        rho = data[:, 1]
        u = data[:, 2]
        v = data[:, 3]
        e = data[:, 4]
        z = data[:, 5]
        p = data[:, 6]
        
        # 绘制多个物理量
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        plt.plot(y, rho)
        plt.xlabel('y')
        plt.ylabel('Density')
        plt.title(f'Density (Step {step}) ({case_name})')
        
        plt.subplot(2, 2, 2)
        plt.plot(y, p)
        plt.xlabel('y')
        plt.ylabel('Pressure')
        plt.title(f'Pressure (Step {step}) ({case_name})')
        
        plt.subplot(2, 2, 3)
        plt.plot(y, z)
        plt.xlabel('y')
        plt.ylabel('Volume Fraction')
        plt.title(f'Volume Fraction (Step {step}) ({case_name})')
        
        plt.subplot(2, 2, 4)
        plt.plot(y, u, label='u')
        plt.plot(y, v, label='v')
        plt.xlabel('y')
        plt.ylabel('Velocity')
        plt.title(f'Velocity Components (Step {step}) ({case_name})')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'lineouty_{step}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"处理完成：{filename} (算例：{case_name})")

def process_masschange_file():
    """处理 masschange 文件"""
    masschange_files = glob.glob(os.path.join(RESULTS_DIR, '*masschange*.dat'))
    if not masschange_files:
        print("未找到 masschange 文件")
        return
    
    file_path = masschange_files[0]
    filename = os.path.basename(file_path)
    
    # 获取算例配置
    case_name, config = get_case_config(filename)
    
    # 读取数据
    data = np.loadtxt(file_path)
    time = data[:, 0]
    mass1 = data[:, 1]
    mass2 = data[:, 2]
    
    # 绘制质量变化
    plt.figure(figsize=(10, 6))
    plt.plot(time, mass1, label='Fluid 1')
    plt.plot(time, mass2, label='Fluid 2')
    plt.xlabel('Time')
    plt.ylabel('Relative Mass Change')
    plt.title(f'Mass Conservation Check ({case_name})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'masschange.png'), dpi=300)
    plt.close()
    
    print(f"处理完成: {filename} (算例: {case_name})")

def create_comparison_plots():
    """创建初始和最终状态的对比图"""
    state_files = sorted(glob.glob(os.path.join(RESULTS_DIR, '*state*.dat')))
    if len(state_files) < 2:
        print("state 文件不足，无法创建对比图")
        return
    
    # 按算例和分辨率分组文件
    files_by_case_resolution = {}
    for file_path in state_files:
        filename = os.path.basename(file_path)
        # 获取算例配置
        case_name, config = get_case_config(filename)
        parts = filename.split('-')
        if len(parts) >= 4:
            try:
                resolution = f"{parts[2]}x{parts[3]}"
                key = f"{case_name}_{resolution}"
                if key not in files_by_case_resolution:
                    files_by_case_resolution[key] = []
                files_by_case_resolution[key].append(file_path)
            except ValueError:
                pass
    
    # 为每种算例和分辨率创建对比图
    for key, files in files_by_case_resolution.items():
        if len(files) >= 2:
            # 初始状态
            initial_file = files[0]
            data_initial = np.loadtxt(initial_file)
            x_initial = data_initial[:, 0]
            y_initial = data_initial[:, 1]
            rho_initial = data_initial[:, 2]
            
            # 最终状态
            final_file = files[-1]
            data_final = np.loadtxt(final_file)
            x_final = data_final[:, 0]
            y_final = data_final[:, 1]
            rho_final = data_final[:, 2]
            
            # 尝试从文件名中提取分辨率信息
            filename = os.path.basename(initial_file)
            case_name, config = get_case_config(filename)
            default_resolution = config['default_resolution']
            parts = filename.split('-')
            Nx, Ny = None, None
            if len(parts) >= 4:
                try:
                    Nx = int(parts[2])
                    Ny = int(parts[3])
                except ValueError:
                    # 如果无法从文件名提取分辨率，将从数据中推断
                    pass
            
            # 如果无法从文件名获取分辨率，从数据中推断
            if Nx is None or Ny is None:
                # 数据点数量
                num_points = len(data_initial)
                # 尝试不同的分辨率组合，找到能整除的
                # 首先尝试默认分辨率
                if num_points == default_resolution[0] * default_resolution[1]:
                    Nx, Ny = default_resolution
                else:
                    # 尝试其他可能的分辨率
                    # 这里简单处理，实际应用中可能需要更复杂的逻辑
                    # 假设 Nx 和 Ny 的比例与默认分辨率相同
                    aspect_ratio = default_resolution[1] / default_resolution[0]
                    # 计算可能的 Nx
                    Nx = int((num_points / aspect_ratio) ** 0.5)
                    Ny = int(num_points / Nx)
                    # 调整以确保 Nx * Ny = num_points
                    while Nx * Ny != num_points and Nx > 0:
                        Nx += 1
                        Ny = int(num_points / Nx)
                    if Nx * Ny != num_points:
                        # 如果仍然无法找到合适的分辨率，使用默认值
                        Nx, Ny = default_resolution
                        print(f"警告：无法从数据中推断分辨率，使用默认值 {Nx}x{Ny}")
                    else:
                        print(f"从数据中推断分辨率：{Nx}x{Ny}")
            
            resolution = f"{Nx}x{Ny}"
            
            # 重塑为网格
            X_initial = x_initial.reshape(Ny, Nx)
            Y_initial = y_initial.reshape(Ny, Nx)
            RHO_initial = rho_initial.reshape(Ny, Nx)
            
            X_final = x_final.reshape(Ny, Nx)
            Y_final = y_final.reshape(Ny, Nx)
            RHO_final = rho_final.reshape(Ny, Nx)
    
            # 计算适合的图像尺寸，基于实际计算域大小
            # 从数据中获取计算域的实际范围
            x_min, x_max = np.min(x_initial), np.max(x_initial)
            y_min, y_max = np.min(y_initial), np.max(y_initial)
            # 计算计算域的宽高比
            domain_width = x_max - x_min
            domain_height = y_max - y_min
            aspect_ratio = domain_width / domain_height
            # 设定基础高度，然后根据宽高比计算宽度（乘 2 是因为有两个子图）
            base_height = 6
            calculated_width = base_height * aspect_ratio * 2
            # 确保宽度和高度在合理范围内
            calculated_width = max(12, min(calculated_width, 24))
            base_height = max(4, min(base_height, 12))
            
            # 获取时间值用于标题显示
            time_initial = float(os.path.basename(initial_file).split('-state-')[1].replace('.dat', ''))
            time_final = float(os.path.basename(final_file).split('-state-')[1].replace('.dat', ''))
            
            # 创建对比图
            plt.figure(figsize=(calculated_width, base_height))
            
            plt.subplot(1, 2, 1)
            im1 = plt.contourf(X_initial, Y_initial, RHO_initial, levels=50, cmap='jet')
            plt.title(f'Initial State at t={time_initial:.6f} ({case_name})')
            plt.xlabel('x')
            plt.ylabel('y')
            plt.colorbar(im1, ax=plt.gca(), label='Density')
            
            plt.subplot(1, 2, 2)
            im2 = plt.contourf(X_final, Y_final, RHO_final, levels=50, cmap='jet')
            plt.title(f'Final State at t={time_final:.6f} ({case_name})')
            plt.xlabel('x')
            plt.ylabel('y')
            plt.colorbar(im2, ax=plt.gca(), label='Density')
            
            plt.tight_layout()
            plt.savefig(os.path.join(PLOTS_DIR, f'comparison_initial_final_{case_name}_{resolution}.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"创建对比图完成 (算例：{case_name}, 分辨率：{resolution})")

def create_gif():
    """从生成的图像创建 GIF 动画"""
    # 收集所有生成的图像 - 支持 6 位小数的文件名
    density_files = glob.glob(os.path.join(PLOTS_DIR, 'density_*.png'))
    interface_files = glob.glob(os.path.join(PLOTS_DIR, 'interface_*.png'))
    pressure_files = glob.glob(os.path.join(PLOTS_DIR, 'pressure_*.png'))
    schlieren_files = glob.glob(os.path.join(PLOTS_DIR, 'schlieren_*.png'))
    
    # 按时间值排序文件 - 改进排序函数以处理 6 位小数
    def get_time_from_image_filename(file_path):
        filename = os.path.basename(file_path)
        # 提取时间部分，支持 6 位小数
        time_str = filename.split('_')[1].replace('.png', '')
        return float(time_str)
    
    density_files = sorted(density_files, key=get_time_from_image_filename)
    interface_files = sorted(interface_files, key=get_time_from_image_filename)
    pressure_files = sorted(pressure_files, key=get_time_from_image_filename)
    schlieren_files = sorted(schlieren_files, key=get_time_from_image_filename)
    
    # 为每种类型创建 GIF
    gif_configs = [
        (density_files, 'density_animation.gif', 'Density Field Animation'),
        (interface_files, 'interface_animation.gif', 'Interface Location Animation'),
        (pressure_files, 'pressure_animation.gif', 'Pressure Field Animation'),
        (schlieren_files, 'schlieren_animation.gif', 'Schlieren Image Animation')
    ]
    
    for files, output_filename, title in gif_configs:
        if len(files) >= 2:
            print(f"创建 {title} GIF...")
            
            # 读取图像
            images = []
            for file_path in files:
                img = imageio.imread(file_path)
                images.append(img)
            
            # 保存 GIF - 提高质量
            output_path = os.path.join(PLOTS_DIR, output_filename)
            imageio.mimsave(output_path, images, duration=0.1, loop=0)
            
            print(f"GIF 保存成功：{output_filename}")
        else:
            print(f"{title} 图像不足，无法创建 GIF")

def main():
    print(f"开始处理结果文件 (时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    
    # 处理各类文件
    process_state_files()
    process_schlieren_files()
    process_lineout_files()
    process_masschange_file()
    create_comparison_plots()
    
    # 创建 GIF 动画
    create_gif()
    
    print(f"处理完成！结果保存在 {PLOTS_DIR} 文件夹中")

if __name__ == "__main__":
    main()
