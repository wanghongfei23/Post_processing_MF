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

# 结果文件夹路径
RESULTS_DIR = 'results'
# 输出图像文件夹
PLOTS_DIR = 'plots'

# 确保输出文件夹存在
os.makedirs(PLOTS_DIR, exist_ok=True)

def process_state_files():
    """处理 state 文件"""
    state_files = sorted(glob.glob(os.path.join(RESULTS_DIR, '*state*.dat')))
    if not state_files:
        print("未找到 state 文件")
        return
    
    print(f"找到 {len(state_files)} 个 state 文件")
    
    for file_path in state_files:
        filename = os.path.basename(file_path)
        time_str = filename.split('-state-')[1].replace('.dat', '')
        time = float(time_str)
        
        # 读取数据
        data = np.loadtxt(file_path)
        x = data[:, 0]
        y = data[:, 1]
        rho = data[:, 2]  # 密度
        z = data[:, 6]     # 体积分数
        p = data[:, 7]     # 压力
        
        # 从文件名中提取分辨率信息
        # 文件名格式: RMI_SF6-MUSCL-100-100-state-0.000000.dat
        parts = filename.split('-')
        if len(parts) >= 4:
            try:
                Nx = int(parts[2])
                Ny = int(parts[3])
            except ValueError:
                # 如果无法从文件名提取分辨率，使用默认值
                Nx, Ny = 1000, 200
        else:
            # 默认分辨率
            Nx, Ny = 1000, 200
        
        # 重塑为二维网格
        X = x.reshape(Ny, Nx)
        Y = y.reshape(Ny, Nx)
        RHO = rho.reshape(Ny, Nx)
        Z = z.reshape(Ny, Nx)
        P = p.reshape(Ny, Nx)
        
        # 绘制密度场
        plt.figure(figsize=(12, 4))
        plt.contourf(X, Y, RHO, levels=50, cmap='jet')
        plt.colorbar(label='Density')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(f'Density Field at t={time:.3f}')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'density_{time:.3f}.png'), dpi=300)
        plt.close()
        
        # 绘制体积分数（界面位置）
        plt.figure(figsize=(12, 4))
        plt.contourf(X, Y, Z, levels=50, cmap='coolwarm')
        plt.colorbar(label='Volume Fraction')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(f'Interface Location at t={time:.3f}')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'interface_{time:.3f}.png'), dpi=300)
        plt.close()
        
        # 绘制压力场
        plt.figure(figsize=(12, 4))
        plt.contourf(X, Y, P, levels=50, cmap='viridis')
        plt.colorbar(label='Pressure')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(f'Pressure Field at t={time:.3f}')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'pressure_{time:.3f}.png'), dpi=300)
        plt.close()
        
        print(f"处理完成: {filename}")

def process_schlieren_files():
    """处理 schlieren 文件"""
    schlieren_files = sorted(glob.glob(os.path.join(RESULTS_DIR, '*schlieren*.dat')))
    if not schlieren_files:
        print("未找到 schlieren 文件")
        return
    
    print(f"找到 {len(schlieren_files)} 个 schlieren 文件")
    
    for file_path in schlieren_files:
        filename = os.path.basename(file_path)
        time_str = filename.split('-schlieren-')[1].replace('.dat', '')
        time = float(time_str)
        
        # 读取数据
        data = np.loadtxt(file_path)
        x = data[:, 0]
        y = data[:, 1]
        grad = data[:, 2]  # 归一化密度梯度
        
        # 从文件名中提取分辨率信息
        # 文件名格式: RMI_SF6-MUSCL-100-100-schlieren-0.000000.dat
        parts = filename.split('-')
        if len(parts) >= 4:
            try:
                Nx = int(parts[2])
                Ny = int(parts[3])
            except ValueError:
                # 如果无法从文件名提取分辨率，使用默认值
                Nx, Ny = 1000, 200
        else:
            # 默认分辨率
            Nx, Ny = 1000, 200
        
        # 重塑为二维网格
        X = x.reshape(Ny, Nx)
        Y = y.reshape(Ny, Nx)
        GRAD = grad.reshape(Ny, Nx)
        
        # 绘制纹影图
        plt.figure(figsize=(12, 4))
        plt.contourf(X, Y, GRAD, levels=50, cmap='gray')
        plt.colorbar(label='Normalized Density Gradient')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(f'Schlieren Image at t={time:.3f}')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'schlieren_{time:.3f}.png'), dpi=300)
        plt.close()
        
        print(f"处理完成: {filename}")

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
        plt.title(f'Density (Step {step})')
        
        plt.subplot(2, 2, 2)
        plt.plot(x, p)
        plt.xlabel('x')
        plt.ylabel('Pressure')
        plt.title(f'Pressure (Step {step})')
        
        plt.subplot(2, 2, 3)
        plt.plot(x, z)
        plt.xlabel('x')
        plt.ylabel('Volume Fraction')
        plt.title(f'Volume Fraction (Step {step})')
        
        plt.subplot(2, 2, 4)
        plt.plot(x, u, label='u')
        plt.plot(x, v, label='v')
        plt.xlabel('x')
        plt.ylabel('Velocity')
        plt.title(f'Velocity Components (Step {step})')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'lineoutx_{step}.png'), dpi=300)
        plt.close()
        
        print(f"处理完成: {filename}")
    
    # 处理 y 方向 lineout
    for file_path in lineouty_files:
        filename = os.path.basename(file_path)
        step = filename.split('-lineouty-')[1].replace('.dat', '')
        
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
        plt.title(f'Density (Step {step})')
        
        plt.subplot(2, 2, 2)
        plt.plot(y, p)
        plt.xlabel('y')
        plt.ylabel('Pressure')
        plt.title(f'Pressure (Step {step})')
        
        plt.subplot(2, 2, 3)
        plt.plot(y, z)
        plt.xlabel('y')
        plt.ylabel('Volume Fraction')
        plt.title(f'Volume Fraction (Step {step})')
        
        plt.subplot(2, 2, 4)
        plt.plot(y, u, label='u')
        plt.plot(y, v, label='v')
        plt.xlabel('y')
        plt.ylabel('Velocity')
        plt.title(f'Velocity Components (Step {step})')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'lineouty_{step}.png'), dpi=300)
        plt.close()
        
        print(f"处理完成: {filename}")

def process_masschange_file():
    """处理 masschange 文件"""
    masschange_files = glob.glob(os.path.join(RESULTS_DIR, '*masschange*.dat'))
    if not masschange_files:
        print("未找到 masschange 文件")
        return
    
    file_path = masschange_files[0]
    filename = os.path.basename(file_path)
    
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
    plt.title('Mass Conservation Check')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'masschange.png'), dpi=300)
    plt.close()
    
    print(f"处理完成: {filename}")

def create_comparison_plots():
    """创建初始和最终状态的对比图"""
    state_files = sorted(glob.glob(os.path.join(RESULTS_DIR, '*state*.dat')))
    if len(state_files) < 2:
        print("state 文件不足，无法创建对比图")
        return
    
    # 按分辨率分组文件
    files_by_resolution = {}
    for file_path in state_files:
        filename = os.path.basename(file_path)
        parts = filename.split('-')
        if len(parts) >= 4:
            try:
                resolution = f"{parts[2]}x{parts[3]}"
                if resolution not in files_by_resolution:
                    files_by_resolution[resolution] = []
                files_by_resolution[resolution].append(file_path)
            except ValueError:
                pass
    
    # 为每种分辨率创建对比图
    for resolution, files in files_by_resolution.items():
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
            
            # 从文件名中提取分辨率信息
            filename = os.path.basename(initial_file)
            parts = filename.split('-')
            try:
                Nx = int(parts[2])
                Ny = int(parts[3])
            except ValueError:
                Nx, Ny = 1000, 200
            
            # 重塑为网格
            X_initial = x_initial.reshape(Ny, Nx)
            Y_initial = y_initial.reshape(Ny, Nx)
            RHO_initial = rho_initial.reshape(Ny, Nx)
            
            X_final = x_final.reshape(Ny, Nx)
            Y_final = y_final.reshape(Ny, Nx)
            RHO_final = rho_final.reshape(Ny, Nx)
    
            # 创建对比图
            plt.figure(figsize=(14, 4))
            
            plt.subplot(1, 2, 1)
            im1 = plt.contourf(X_initial, Y_initial, RHO_initial, levels=50, cmap='jet')
            plt.title('Initial State')
            plt.xlabel('x')
            plt.ylabel('y')
            plt.colorbar(im1, ax=plt.gca(), label='Density')
            
            plt.subplot(1, 2, 2)
            im2 = plt.contourf(X_final, Y_final, RHO_final, levels=50, cmap='jet')
            plt.title('Final State')
            plt.xlabel('x')
            plt.ylabel('y')
            plt.colorbar(im2, ax=plt.gca(), label='Density')
            
            plt.tight_layout()
            plt.savefig(os.path.join(PLOTS_DIR, f'comparison_initial_final_{resolution}.png'), dpi=300)
            plt.close()
            
            print(f"创建对比图完成 (分辨率: {resolution})")

def main():
    print(f"开始处理结果文件 (时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    
    # 处理各类文件
    process_state_files()
    process_schlieren_files()
    process_lineout_files()
    process_masschange_file()
    create_comparison_plots()
    
    print(f"处理完成！结果保存在 {PLOTS_DIR} 文件夹中")

if __name__ == "__main__":
    main()
