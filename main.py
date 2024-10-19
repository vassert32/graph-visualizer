import csv
import subprocess
import sys
import os

def parse_config(config_path):
    with open(config_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        config = next(reader)
        graphviz_path, repo_path, output_path = config
        # Удаляем кавычки из путей, если они есть
        graphviz_path = graphviz_path.strip('"')
        repo_path = repo_path.strip('"')
        output_path = output_path.strip('"')
        return graphviz_path, repo_path, output_path

def get_commits(repo_path, max_count=10):
    cmd = f'git -C "{repo_path}" rev-list --max-count={max_count} --all'
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', shell=True)
    if result.returncode != 0:
        print(f"Ошибка при выполнении команды git: {result.stderr}")
        sys.exit(1)
    commits = result.stdout.strip().split('\n')
    commits.reverse()  # в хронологическом порядке
    return commits

def get_commit_files(repo_path, commit_hash):
    cmd = f'git -C "{repo_path}" diff-tree --no-commit-id --name-only -r {commit_hash}'
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', shell=True)
    if result.returncode != 0:
        print(f"Ошибка при выполнении команды git: {result.stderr}")
        sys.exit(1)
    files = result.stdout.strip().split('\n')
    return files

def get_commit_parents(repo_path, commit_hash):
    cmd = f'git -C "{repo_path}" rev-list --parents -n 1 {commit_hash}'
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', shell=True)
    if result.returncode != 0:
        print(f"Ошибка при выполнении команды git: {result.stderr}")
        sys.exit(1)
    parts = result.stdout.strip().split()
    return parts[1:] if len(parts) > 1 else []

def get_commit_message(repo_path, commit_hash):
    cmd = f'git -C "{repo_path}" log -n 1 --pretty=format:%s {commit_hash}'
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', shell=True)
    if result.returncode != 0:
        print(f"Ошибка при получении сообщения коммита: {result.stderr}")
        sys.exit(1)
    message = result.stdout.strip()
    return message

def build_dependency_graph(repo_path, commits):
    graph = {}
    for commit in commits:
        files = get_commit_files(repo_path, commit)
        parents = get_commit_parents(repo_path, commit)
        message = get_commit_message(repo_path, commit)
        # Используем полные хэши коммитов
        graph[commit] = {
            'message': message,
            'files': files,
            'parents': parents
        }
    return graph

def generate_graphviz_code(graph):
    lines = ['digraph G {']
    # Настройки графа для лучшего отображения
    lines.append('    node [shape=box, style=filled, fillcolor="#D3D3D3"];')
    lines.append('    rankdir=TB;')  # Расположение графа сверху вниз
    for commit, data in graph.items():
        # Экранируем кавычки в сообщении коммита
        label_message = data['message'].replace('"', '\\"')
        # Экранируем обратные слеши и кавычки в именах файлов
        label_files_list = [file.replace('\\', '\\\\').replace('"', '\\"') for file in data['files']]
        # Объединяем имена файлов с помощью \n
        label_files = "\\n".join(label_files_list)
        # Ограничим длину списка файлов, если он слишком большой
        if len(label_files) > 200:
            label_files = label_files[:200] + '\\n...'
        # Формируем метку узла
        label = f"Commit: {commit}\\nMessage: {label_message}\\nFiles:\\n{label_files}"
        lines.append(f'"{commit}" [label="{label}"];')
        for parent in data['parents']:
            lines.append(f'"{parent}" -> "{commit}";')
    lines.append('}')
    return '\n'.join(lines)

def output_result(graphviz_code, output_path):
    print("Код Graphviz сгенерирован и сохранен в файл.")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(graphviz_code)

def generate_image(graphviz_path, dot_path, output_image_path):
    cmd = f'"{graphviz_path}" -Tpng "{dot_path}" -o "{output_image_path}" -Gdpi=300'
    print(f"Выполняется команда: {cmd}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='cp1251',  # Используем кодировку Windows для русского языка
        shell=True
    )
    if result.returncode != 0:
        print(f"Ошибка при генерации изображения Graphviz: {result.stderr}")
        sys.exit(1)
    else:
        print(f"Изображение графа успешно сгенерировано: {output_image_path}")

def main(config_path):
    graphviz_path, repo_path, output_path = parse_config(config_path)
    commits = get_commits(repo_path, 15)
    graph = build_dependency_graph(repo_path, commits)
    graphviz_code = generate_graphviz_code(graph)
    output_result(graphviz_code, output_path)

    output_image_path = os.path.splitext(output_path)[0] + '.png'
    generate_image(graphviz_path, output_path, output_image_path)

if __name__ == '__main__':
    main('config.csv')
