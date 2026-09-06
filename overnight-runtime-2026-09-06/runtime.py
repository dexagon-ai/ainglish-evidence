"""Small offline experiment runtime: durable calls, exact tokens, no uncertain retries.

This is research infrastructure, not an alternative to Ainglish mint-before-spend.
Governance runners must still preregister through the official SDK.
"""
from __future__ import annotations
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

GIB = 1024 ** 3

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def save_new(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as out:
        out.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
        out.flush(); os.fsync(out.fileno())

def disk_guard(host='/mnt/c', workspace='/home/dexagon', host_reserve=15*GIB,
               workspace_reserve=5*GIB, usage=shutil.disk_usage):
    # Never substitute Linux's optimistic VHD free space for physical host capacity.
    values = {'host_free_bytes': usage(host).free, 'workspace_free_bytes': usage(workspace).free}
    if values['host_free_bytes'] < host_reserve:
        raise RuntimeError('Physical host reserve reached; stop before another call or checkpoint')
    if values['workspace_free_bytes'] < workspace_reserve:
        raise RuntimeError('Workspace reserve reached; stop before another call or checkpoint')
    return values

def preallocate_gpu_guard(index='0'):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != index:
        raise RuntimeError('Explicit physical GPU isolation is required')
    raw = subprocess.check_output(['nvidia-smi', '-i', index,
        '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True)
    used, util = [int(v.strip()) for v in raw.strip().split(',')]
    if used > 512 or util > 5:
        raise RuntimeError('Selected GPU is occupied; no eviction or service changes')
    return {'physical_gpu': index, 'memory_used_mib': used, 'utilization_percent': util}

class Journal:
    """Single-writer hash chain. Resume only completed calls; refuse uncertain spend."""
    def __init__(self, path, plan, *, resume=False):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open('a+' if resume else 'x+')
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.handle.seek(0)
            self.events = self._validate(self.handle.read())
            self.completed = {}
            self.pending = {}
            self.plan_hash = digest(plan)
            if self.events:
                if self.events[0]['kind'] != 'plan' or self.events[0]['data'] != plan:
                    raise RuntimeError('Resume plan differs from the original commitment')
                for event in self.events[1:]:
                    key = event['data'].get('call_id')
                    if event['kind'] == 'begin':
                        if key in self.pending or key in self.completed:
                            raise RuntimeError('Repeated call id in journal')
                        self.pending[key] = event['data']
                    elif event['kind'] == 'end':
                        if key not in self.pending:
                            raise RuntimeError('Completion without spend intent')
                        if event['data']['request_hash'] != self.pending[key]['request_hash']:
                            raise RuntimeError('Completion does not match call intent')
                        self.completed[key] = event['data']; del self.pending[key]
                if self.pending:
                    raise RuntimeError('Uncertain in-flight calls retained; reconcile without retrying inference')
            else:
                self.append('plan', plan)
        except BaseException:
            self.handle.close(); raise

    @staticmethod
    def _validate(raw):
        if raw and not raw.endswith('\n'):
            raise RuntimeError('Partial final journal row; do not silently truncate or replay')
        result = []; previous = None
        for index, line in enumerate(raw.splitlines()):
            event = json.loads(line)
            claimed = event.pop('hash')
            if event['seq'] != index or event['previous'] != previous or digest(event) != claimed:
                raise RuntimeError('Journal integrity failure')
            event['hash'] = claimed; result.append(event); previous = claimed
        return result

    def append(self, kind, data):
        event = {'seq': len(self.events), 'previous': self.events[-1]['hash'] if self.events else None,
                 'kind': kind, 'at_unix': time.time(), 'data': data}
        event['hash'] = digest(event)
        self.handle.seek(0, os.SEEK_END); self.handle.write(canonical(event).decode()+'\n')
        self.handle.flush(); os.fsync(self.handle.fileno()); self.events.append(event)

    def lookup(self, call_id, request):
        result = self.completed.get(call_id)
        if result is not None and result['request_hash'] != digest(request):
            raise RuntimeError('Call id reused for changed prompt, budget or metadata')
        return result

    def begin(self, call_id, request):
        if call_id in self.pending or call_id in self.completed:
            raise RuntimeError('Call already started; no duplicate spend')
        data = {'call_id': call_id, 'request_hash': digest(request), 'request': request}
        self.append('begin', data); self.pending[call_id] = data

    def end(self, call_id, result):
        if call_id not in self.pending: raise RuntimeError('No pending call')
        data = {**result, 'call_id': call_id, 'request_hash': self.pending[call_id]['request_hash']}
        self.append('end', data); self.completed[call_id] = data; del self.pending[call_id]
        return data

    def close(self): self.handle.close()
    def __enter__(self): return self
    def __exit__(self, *args): self.close()

def verify_freeze(root):
    root = Path(root)
    pins = json.loads((root/'FROZEN.json').read_text())
    for name, expected in pins.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'Frozen source drift: {name}')
    relative = (root/'FROZEN.json').relative_to(root.parent).as_posix()
    commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', relative], cwd=root.parent, text=True).strip()
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'origin/main'], cwd=root.parent, check=True)
    for name in [*pins, 'FROZEN.json']:
        path = (root/name).resolve().relative_to(root.parent.resolve()).as_posix()
        if subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=root.parent) != (root/name).read_bytes():
            raise RuntimeError(f'Unpublished or changed source: {name}')
    return commit

class LocalReader:
    """One already cached HF reader, strictly offline, with exact generated IDs."""
    def __init__(self, snapshot):
        for name in ['HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE']:
            os.environ[name] = '1'
        disk_guard(); device = preallocate_gpu_guard()
        snapshot = Path(snapshot)
        if not snapshot.is_dir(): raise RuntimeError('Pinned cache absent; no downloads')
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, set_seed
        if torch.cuda.device_count() != 1: raise RuntimeError('One visible GPU required')
        if torch.cuda.mem_get_info()[0] < 16*GIB: raise RuntimeError('Insufficient VRAM')
        set_seed(20260906)
        self.tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
            bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
        self.model = AutoModelForCausalLM.from_pretrained(str(snapshot), local_files_only=True,
            quantization_config=quant, device_map={'': 0}, torch_dtype=torch.bfloat16)
        self.model.eval(); self.model.config.use_cache = True
        import importlib.metadata
        self.provenance = {**device, 'snapshot': str(snapshot), 'revision': snapshot.name,
            'tokenizer_sha256': hashlib.sha256((snapshot/'tokenizer.json').read_bytes()).hexdigest(),
            'quantization': 'bitsandbytes-nf4-double-quant-bfloat16', 'seed': 20260906,
            'versions': {n: importlib.metadata.version(n) for n in ['torch', 'transformers', 'bitsandbytes', 'tokenizers']},
            'downloads': 0, 'governance_evidence': False}

    def call(self, journal, call_id, messages, *, cap=512, metadata=None, max_prompt_tokens=4096):
        request = {'messages': messages, 'max_new_tokens': cap, 'metadata': metadata,
                   'max_prompt_tokens': max_prompt_tokens, 'do_sample': False}
        old = journal.lookup(call_id, request)
        if old is not None: return old
        disk_guard()
        import torch
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        encoded = self.tokenizer(prompt, return_tensors='pt', add_special_tokens=False).to(self.model.device)
        input_ids = encoded['input_ids'][0].tolist()
        if len(input_ids) > max_prompt_tokens: raise RuntimeError('Prompt budget exceeded before spend')
        journal.begin(call_id, request)
        started = time.time()
        with torch.inference_mode():
            generated = self.model.generate(**encoded, max_new_tokens=cap, do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id, eos_token_id=self.tokenizer.eos_token_id)
        tokens = generated[0, len(input_ids):].tolist()
        ended = self.tokenizer.eos_token_id in tokens
        if ended: tokens = tokens[:tokens.index(self.tokenizer.eos_token_id)+1]
        raw = self.tokenizer.decode(tokens, skip_special_tokens=True)
        return journal.end(call_id, {'raw': raw, 'ended': ended, 'input_ids': input_ids,
            'output_ids': tokens, 'input_tokens': len(input_ids), 'output_tokens': len(tokens),
            'latency_s': time.time()-started, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()})
