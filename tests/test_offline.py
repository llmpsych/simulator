"""Regression tests use synthetic text and temporary output, never model calls."""
from datetime import datetime
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_test as runner
from scripts.check_offline import ROOT, check_data, read_json


class SimulatorTests(unittest.TestCase):
    def test_cli_defaults_and_overrides(self):
        with patch('sys.argv', ['run_test.py', 'example_v001']):
            args = runner.parse_args()
        self.assertEqual((args.prompt, args.patient, args.bot, args.turns),
                         ('example_v001', 'qwen3:30b', 'mistral:7b', 10))
        with patch('sys.argv', ['run_test.py', 'example_v001', '--patient', 'p', '--bot', 'b', '--turns', '2']):
            args = runner.parse_args()
        self.assertEqual((args.patient, args.bot, args.turns), ('p', 'b', 2))

    def test_conversation_histories_and_saved_transcript(self):
        calls = []
        responses = iter(['patient one', 'bot one', 'patient two', 'bot two'])

        def respond(model, messages, system=None):
            calls.append((model, copy.deepcopy(messages), system))
            return next(responses)

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(runner, 'TRANSCRIPTS_DIR', Path(directory)), \
                 patch.object(runner, 'call_ollama', side_effect=respond), \
                 patch.object(runner, 'datetime') as clock, \
                 contextlib.redirect_stdout(io.StringIO()):
                clock.now.return_value = datetime(2026, 1, 2, 3, 4, 5)
                transcript = runner.run_test('001_exhausted_resources_v002', 'patient-model', 'bot-model', 2)
            files = list(Path(directory).glob('*.json'))
            self.assertEqual(len(files), 1)
            saved = read_json(files[0])
        self.assertEqual([row['content'] for row in transcript],
                         ['patient one', 'bot one', 'patient two', 'bot two'])
        self.assertEqual([row['role'] for row in transcript], ['patient', 'bot'] * 2)
        self.assertEqual(saved['transcript'], transcript)
        self.assertEqual(saved['metadata']['timestamp'], '20260102_030405')
        self.assertEqual(saved['metadata']['prompt'], '001_exhausted_resources_v002')
        self.assertEqual(saved['metadata']['case'], '001_exhausted_resources')
        self.assertEqual(saved['metadata']['patient_model'], 'patient-model')
        self.assertEqual(saved['metadata']['bot_model'], 'bot-model')
        self.assertEqual([c[0] for c in calls], ['patient-model', 'bot-model'] * 2)
        self.assertEqual(calls[2][1], [{'role': 'assistant', 'content': 'patient one'},
                                     {'role': 'user', 'content': 'bot one'}])
        self.assertEqual(calls[3][1], [{'role': 'user', 'content': 'patient one'},
                                     {'role': 'assistant', 'content': 'bot one'},
                                     {'role': 'user', 'content': 'patient two'}])
        self.assertEqual(calls[0][2], runner.load_prompt('001_exhausted_resources_v002'))
        self.assertEqual(calls[2][2], calls[0][2])
        self.assertIsNone(calls[1][2])
        self.assertIsNone(calls[3][2])

    def test_ollama_payload_without_transport(self):
        messages = [{'role': 'user', 'content': 'synthetic input'}]
        with patch.object(runner.subprocess, 'run') as transport:
            transport.return_value.stdout = '{"message":{"content":"synthetic reply"}}'
            self.assertEqual(runner.call_ollama('mock-model', messages, 'system prompt'), 'synthetic reply')
        payload = json.loads(transport.call_args.args[0][-1])
        self.assertEqual(payload['model'], 'mock-model')
        self.assertFalse(payload['stream'])
        self.assertEqual(payload['messages'], [{'role': 'system', 'content': 'system prompt'}] + messages)
        self.assertEqual(payload['options'], {'num_ctx': 32768, 'repeat_penalty': 1.1, 'mirostat': 2})
        self.assertEqual(messages, [{'role': 'user', 'content': 'synthetic input'}])

    def test_transport_response_fallbacks(self):
        for response, expected in [('{}', 'ERROR: No content'), ('not json', 'ERROR: not json')]:
            with self.subTest(response=response), patch.object(runner.subprocess, 'run') as transport:
                transport.return_value.stdout = response
                self.assertEqual(runner.call_ollama('mock', []), expected)

    def test_missing_prompt_fails_before_model_call(self):
        with patch.object(runner, 'call_ollama') as model:
            with self.assertRaises(FileNotFoundError):
                runner.run_test('missing', 'patient', 'bot', 1)
            model.assert_not_called()

    def test_fixture_validator_rejects_corruptions(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['cases', 'prompts', 'transcripts']:
                shutil.copytree(ROOT / name, root / name)
            path = sorted((root / 'transcripts').glob('*.json'))[0]
            original = read_json(path)
            for kind in ['role', 'prompt', 'incomplete', 'empty']:
                data = copy.deepcopy(original)
                if kind == 'role':
                    data['transcript'][0]['role'] = 'bot'
                elif kind == 'prompt':
                    data['metadata']['prompt'] = 'missing_v001'
                elif kind == 'incomplete':
                    data['transcript'].pop()
                else:
                    data['transcript'][0]['content'] = ''
                path.write_text(json.dumps(data))
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    check_data(root)

    def test_strict_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'invalid.json'
            for content in ['{"x":1,"x":2}', '{"x":NaN}', '{broken']:
                path.write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError):
                    read_json(path)
