# 自动检测并忽略大于 100MB 的文件
# 命令行：python .admin_script/auto_ignore_large_files_v2.py

import os
import sys

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
    """查找大于指定大小的文件"""
    size_limit_bytes = size_limit_mb * 1024 * 1024
    large_files = []

    for root, dirs, files in os.walk(directory):
        # 跳过 .git 目录
        if '.git' in root.split(os.sep):
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                if file_size > size_limit_bytes:
                    # 获取相对路径
                    relative_path = os.path.relpath(file_path, directory)
                    large_files.append(relative_path)
            except (OSError, PermissionError):
                pass

    return large_files

def update_gitignore(files_to_ignore, gitignore_path='.gitignore'):
    """更新 .gitignore 文件"""
    
    # 读取现有的 .gitignore 内容
    existing_content = ""
    existing_lines = []
    existing_patterns = set()
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_lines = f.readlines()
            existing_content = ''.join(existing_lines)
            existing_patterns = set(line.strip() for line in existing_lines if line.strip())
    
    # 添加新的大文件忽略规则
    new_patterns = []
    header = "# 自动忽略的大文件 (>100MB)"
    
    for file_path in files_to_ignore:
        # 统一使用正斜杠
        pattern = file_path.replace('\\', '/')
        if pattern not in existing_patterns:
            new_patterns.append(pattern)
    
    # 检查并移除已删除的文件
    removed_patterns = []
    if existing_content:
        # 提取所有可能的忽略模式（排除注释和空行）
        for line in existing_lines:
            pattern = line.strip()
            if pattern and not pattern.startswith('#'):
                # 检查文件是否存在
                # 处理路径分隔符
                file_path = pattern.replace('/', '\\')
                if not os.path.exists(file_path):
                    removed_patterns.append(pattern)
    
    # 重新构建 .gitignore 内容
    if removed_patterns:
        # 过滤掉已删除文件的规则
        new_lines = []
        for line in existing_lines:
            pattern = line.strip()
            if pattern and pattern not in removed_patterns:
                new_lines.append(line)
            elif not pattern or pattern.startswith('#'):
                new_lines.append(line)
        
        # 写入更新后的内容
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        for pattern in removed_patterns:
            print(f"  {Colors.RED}- 移除: {pattern} (文件已删除){Colors.END}")
        
        print(f"\n{Colors.GREEN}✓ 已从 .gitignore 中移除 {len(removed_patterns)} 个已删除的文件{Colors.END}")
    
    if not new_patterns and not removed_patterns:
        print(f"{Colors.GREEN}✓ 没有新的大文件需要添加到 .gitignore，也没有已删除的文件需要移除{Colors.END}")
        return
    
    # 添加新的大文件忽略规则
    if new_patterns:
        with open(gitignore_path, 'a', encoding='utf-8') as f:
            if existing_content and not existing_content.endswith('\n'):
                f.write('\n')
            
            if header not in existing_content:
                f.write(f"\n{header}\n")
            
            for pattern in new_patterns:
                f.write(f"{pattern}\n")
                print(f"  {Colors.YELLOW}+ 添加: {pattern}{Colors.END}")
        
        print(f"\n{Colors.GREEN}✓ 已将 {len(new_patterns)} 个大文件添加到 .gitignore{Colors.END}")

def main():
    print(f"{Colors.CYAN}{'=' * 100}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'自动忽略大文件工具 (v2)':^100}{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 100}{Colors.END}")
    
    # 查找大文件
    print(f"\n{Colors.BLUE}正在扫描大于 100MB 的文件...{Colors.END}")
    large_files = find_large_files('.')
    
    if not large_files:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 没有找到大于 100MB 的文件{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}发现 {len(large_files)} 个大于 100MB 的文件:{Colors.END}")
        print(f"{Colors.YELLOW}{'-' * 100}{Colors.END}")
        
        for file_path in large_files:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"  {Colors.YELLOW}- {file_path} ({size_mb:.2f} MB){Colors.END}")
        
        print(f"{Colors.YELLOW}{'-' * 100}{Colors.END}")
    
    # 更新 .gitignore
    print(f"\n{Colors.BLUE}正在更新 .gitignore...{Colors.END}")
    update_gitignore(large_files)
    
    print(f"\n{Colors.CYAN}{'=' * 100}{Colors.END}")
    print(f"{Colors.YELLOW}{Colors.BOLD}提示：如果文件已被 Git 跟踪，请运行以下命令：{Colors.END}")
    print(f"  {Colors.CYAN}git rm --cached <文件路径>{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 100}{Colors.END}")

if __name__ == '__main__':
    main()