# 检测 Git 仓库中的大文件
# 命令行：python .admin_script/check_large_files.py

import os

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def find_large_files(directory='.', size_limit_mb=100):
    size_limit_bytes = size_limit_mb * 1024 * 1024
    large_files_git = []
    large_files_nongit = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                if file_size > size_limit_bytes:
                    if '.git' in file_path.split(os.sep):
                        large_files_nongit.append((file_path, file_size))
                    else:
                        large_files_git.append((file_path, file_size))
            except (OSError, PermissionError) as e:
                print(f"无法访问文件 {file_path}: {e}")

    return large_files_git, large_files_nongit

def print_table(files, title, color):
    if not files:
        return
    
    print(f"\n{color}{Colors.BOLD}{title}{Colors.END}")
    print(f"{color}{'=' * 100}{Colors.END}")
    
    header = f"{color}{'序号':<6}{'文件路径':<60}{'大小 (MB)':<15}{'大小 (字节)':<20}{Colors.END}"
    print(header)
    print(f"{color}{'-' * 100}{Colors.END}")
    
    for idx, (file_path, file_size) in enumerate(files, 1):
        size_mb = file_size / (1024 * 1024)
        relative_path = file_path.replace(os.getcwd(), '.')
        row = f"{color}{idx:<6}{relative_path:<60}{size_mb:>10.2f} MB{file_size:>15,} 字节{Colors.END}"
        print(row)
    
    print(f"{color}{'=' * 100}{Colors.END}")

if __name__ == '__main__':
    current_dir = os.getcwd()
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 100}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'大文件检测工具':^100}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 100}{Colors.END}")
    print(f"{Colors.WHITE}扫描目录: {current_dir}{Colors.END}")
    print(f"{Colors.WHITE}查找大于 100MB 的文件...{Colors.END}")

    large_files_git, large_files_nongit = find_large_files(current_dir)

    if large_files_git:
        print_table(large_files_git, f"⚠️  找到 {len(large_files_git)} 个超过 100MB 的文件（会被 Git 提交，需要处理）", Colors.RED)
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 没有找到超过 100MB 的文件（会被 Git 提交的文件）{Colors.END}")

    if large_files_nongit:
        print_table(large_files_nongit, f"ℹ️  找到 {len(large_files_nongit)} 个超过 100MB 的文件（.git 文件夹内，不会被提交）", Colors.GREEN)
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 没有找到超过 100MB 的文件（.git 文件夹内）{Colors.END}")

    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 100}{Colors.END}")
    print(f"{Colors.YELLOW}{Colors.BOLD}提示: 红色表格中的文件会影响 Git 提交，请添加到 .gitignore 或删除{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 100}{Colors.END}")
