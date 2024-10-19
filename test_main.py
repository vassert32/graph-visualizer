import unittest
from unittest.mock import patch, mock_open, MagicMock
import subprocess
import sys
import os

# Предполагается, что main.py находится в той же директории
from main import (
    parse_config,
    get_commits,
    get_commit_files,
    get_commit_parents,
    get_commit_message,
    build_dependency_graph,
    generate_graphviz_code,
    output_result
)

class TestDependencyVisualizer(unittest.TestCase):

    def test_parse_config(self):
        # Тестирование функции parse_config
        test_csv_content = '"C:\\Program Files\\Graphviz\\bin\\dot.exe","C:\\path\\to\\repo","C:\\path\\to\\output.dot"\n'
        with patch('builtins.open', mock_open(read_data=test_csv_content)):
            graphviz_path, repo_path, output_path = parse_config('config.csv')
            self.assertEqual(graphviz_path, 'C:\\Program Files\\Graphviz\\bin\\dot.exe')
            self.assertEqual(repo_path, 'C:\\path\\to\\repo')
            self.assertEqual(output_path, 'C:\\path\\to\\output.dot')

    @patch('subprocess.run')
    def test_get_commits(self, mock_run):
        # Тестирование функции get_commits
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='commit_hash_1\ncommit_hash_2\n', stderr=''
        )
        commits = get_commits('C:\\path\\to\\repo', max_count=2)
        self.assertEqual(commits, ['commit_hash_2', 'commit_hash_1'])  # Проверяем, что список перевернут

    @patch('subprocess.run')
    def test_get_commit_files(self, mock_run):
        # Тестирование функции get_commit_files
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='file1.py\nfile2.py\n', stderr=''
        )
        files = get_commit_files('C:\\path\\to\\repo', 'commit_hash_1')
        self.assertEqual(files, ['file1.py', 'file2.py'])

    @patch('subprocess.run')
    def test_get_commit_parents(self, mock_run):
        # Тестирование функции get_commit_parents
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='commit_hash_1 parent_hash_1 parent_hash_2\n', stderr=''
        )
        parents = get_commit_parents('C:\\path\\to\\repo', 'commit_hash_1')
        self.assertEqual(parents, ['parent_hash_1', 'parent_hash_2'])

    @patch('subprocess.run')
    def test_get_commit_message(self, mock_run):
        # Тестирование функции get_commit_message
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='Initial commit\n', stderr=''
        )
        message = get_commit_message('C:\\path\\to\\repo', 'commit_hash_1')
        self.assertEqual(message, 'Initial commit')

    def test_build_dependency_graph(self):
        # Тестирование функции build_dependency_graph
        commits = ['commit_hash_1', 'commit_hash_2']
        with patch('main.get_commit_files') as mock_get_files, \
             patch('main.get_commit_parents') as mock_get_parents, \
             patch('main.get_commit_message') as mock_get_message:

            mock_get_files.side_effect = [['file1.py'], ['file2.py', 'file3.py']]
            mock_get_parents.side_effect = [['parent_hash_1'], ['commit_hash_1']]
            mock_get_message.side_effect = ['Initial commit', 'Added new features']

            graph = build_dependency_graph('C:\\path\\to\\repo', commits)

            expected_graph = {
                'commit_hash_1': {
                    'message': 'Initial commit',
                    'files': ['file1.py'],
                    'parents': ['parent_hash_1']
                },
                'commit_hash_2': {
                    'message': 'Added new features',
                    'files': ['file2.py', 'file3.py'],
                    'parents': ['commit_hash_1']
                }
            }

            self.assertEqual(graph, expected_graph)

    def test_generate_graphviz_code(self):
        # Тестирование функции generate_graphviz_code
        graph = {
            'commit_hash_1': {
                'message': 'Initial commit',
                'files': ['file1.py'],
                'parents': ['parent_hash_1']
            },
            'commit_hash_2': {
                'message': 'Added new features',
                'files': ['file2.py', 'file3.py'],
                'parents': ['commit_hash_1']
            }
        }

        expected_code = (
            'digraph G {\n'
            '    node [shape=box, style=filled, fillcolor="#D3D3D3"];\n'
            '    rankdir=TB;\n'
            '"commit_hash_1" [label="Commit: commit_hash_1\\nMessage: Initial commit\\nFiles:\\nfile1.py"];\n'
            '"parent_hash_1" -> "commit_hash_1";\n'
            '"commit_hash_2" [label="Commit: commit_hash_2\\nMessage: Added new features\\nFiles:\\nfile2.py\\nfile3.py"];\n'
            '"commit_hash_1" -> "commit_hash_2";\n'
            '}'
        )

        graphviz_code = generate_graphviz_code(graph)
        self.assertEqual(graphviz_code.strip(), expected_code.strip())

    @patch('builtins.open', new_callable=mock_open)
    def test_output_result(self, mock_file):
        # Тестирование функции output_result
        graphviz_code = 'digraph G { ... }'
        output_result(graphviz_code, 'C:\\path\\to\\output.dot')

        # Проверяем, что файл был открыт для записи
        mock_file.assert_called_once_with('C:\\path\\to\\output.dot', 'w', encoding='utf-8')
        # Проверяем, что данные были записаны в файл
        mock_file().write.assert_called_once_with(graphviz_code)

    # Мы не будем тестировать функцию generate_image, так как она вызывает внешнюю программу

if __name__ == '__main__':
    unittest.main()
