#!/usr/bin/env python3
"""Phase 0 checks only. Never downloads, uploads, or overwrites a user ROM."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/phase0'
LOCK = json.loads((ROOT / 'config/phase0.lock.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, obj):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / name).write_text(json.dumps(obj, indent=2) + '\n')


def command(argv, cwd=ROOT, log=None):
    if log:
        with (EVIDENCE / log).open('a') as output:
            output.write(json.dumps({'command':list(map(str, argv)), 'cwd':str(cwd)})+'\n')
            output.flush()
            result = subprocess.run(argv, cwd=cwd, stdout=output, stderr=subprocess.STDOUT)
            output.write(f'EXIT_CODE={result.returncode}\n')
    else:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'Command exited {result.returncode}: {argv}; evidence: {log}')
    return result


def verify_tools():
    results = []
    for name, entry in LOCK['toolchain']['binaries'].items():
        path = Path(entry['path'])
        results.append({'tool': name, 'path': str(path), 'passed': path.is_file() and sha(path) == entry['sha256']})
    agbcc_root = Path(LOCK['toolchain']['binaries']['agbcc']['path']).parent
    headers_ok = all((agbcc_root / e['path']).is_file() and sha(agbcc_root / e['path']) == e['sha256'] for e in LOCK['toolchain']['headers'])
    results.append({'tool':'agbcc headers', 'passed':headers_ok, 'files_checked':len(LOCK['toolchain']['headers'])})
    return results


def doctor():
    results = verify_tools()
    for key, args in [('upstream', ['git','cat-file','-e',LOCK['source']['commit']+'^{commit}']),
                      ('libpng', ['pkg-config','--modversion','libpng'])]:
        p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        ok = p.returncode == 0
        if key == 'libpng':
            ok = ok and p.stdout.strip() == LOCK['toolchain']['versions']['libpng']
        results.append({'tool':key,'passed':ok,'command':args,'exit_code':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()})
    write('doctor.json', {'scope':'build prerequisites only; emulator and gameplay are separate', 'checks':results})
    if not all(x['passed'] for x in results):
        raise RuntimeError('Pinned prerequisite mismatch: see evidence/phase0/doctor.json')
    print(f'Doctor: {len(results)} pinned build prerequisite checks passed; no emulator claim.')


def baseline():
    doctor()
    local = ROOT / '.local'
    local.mkdir(exist_ok=True)
    source = Path(tempfile.mkdtemp(prefix='baseline-', dir=local))
    log = 'baseline-wrapper.log'
    (EVIDENCE / log).write_text('Fresh source export; no reuse of build products.\n')
    with tempfile.TemporaryFile() as archive:
        p = subprocess.run(['git','archive',LOCK['source']['commit']], cwd=ROOT, stdout=archive)
        if p.returncode:
            raise RuntimeError('Could not export pinned source')
        archive.seek(0)
        with tarfile.open(fileobj=archive) as package:
            package.extractall(source, filter='data')
    agbcc_source = Path(LOCK['toolchain']['binaries']['agbcc']['path']).parent
    installed = source / 'tools/agbcc'
    (installed / 'bin').mkdir(parents=True)
    (installed / 'lib').mkdir()
    # Exact installation operations from pinned agbcc/install.sh, without shell path interpolation.
    shutil.copytree(agbcc_source / 'libc/include', installed / 'include')
    for p in (agbcc_source / 'ginclude').iterdir():
        if p.is_file():
            shutil.copy2(p, installed / 'include' / p.name)
    for name in ['agbcc','old_agbcc','agbcc_arm']:
        shutil.copy2(agbcc_source / name, installed / 'bin' / name)
    for name in ['libgcc.a','libc.a']:
        shutil.copy2(agbcc_source / name, installed / 'lib' / name)
    command(['make','-j8','compare','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0'], source, log)
    rom = source / 'pokefirered.gba'
    data = rom.read_bytes()
    target = LOCK['source']['target']
    result = {'source_commit': LOCK['source']['commit'], 'source_directory': str(source.relative_to(ROOT)),
              'target': target, 'size':len(data), 'sha1':hashlib.sha1(data).hexdigest(), 'sha256':sha(rom),
              'clean_source_export':True,'upstream_compare_exit_code':0,'log':'evidence/phase0/'+log,
              'rom_path':str(rom.relative_to(ROOT)), 'elf_sha256':sha(source/'pokefirered.elf'),
              'map_sha256':sha(source/'pokefirered.map')}
    result['passed'] = all(result[k] == target[k] for k in ['sha1','sha256','size'])
    write('baseline.json',result)
    if not result['passed']:
        raise RuntimeError('Baseline hash mismatch')
    print('Fresh baseline matches SHA-1 and SHA-256; private products in '+str(source.relative_to(ROOT)))


def test_host():
    result = command([sys.executable, 'pokemon_influencer_handoff/tools/validate_handoff.py'])
    print(result.stdout)
    print('This validates the handoff only. No host runtime or gameplay tests exist.')


def inspect_dump(path):
    path = path.resolve()
    data = path.read_bytes()
    if len(data) < 192:
        raise RuntimeError('Not a complete GBA header')
    target = LOCK['source']['target']
    report = {'path':os.path.relpath(path, ROOT),'size':len(data),'sha1':hashlib.sha1(data).hexdigest(),
              'sha256':hashlib.sha256(data).hexdigest(),'title':data[160:172].decode('ascii',errors='replace'),
              'game_code':data[172:176].decode('ascii',errors='replace'),'revision':data[188],
              'header_check_valid':((-sum(data[160:189])-25)&255)==data[189], 'read_only':True}
    report['matches_supported_target'] = all(report[k] == target[k] for k in ['sha1','sha256','size'])
    write('dump-verification.json', report)
    print(json.dumps(report,indent=2))
    if not report['matches_supported_target']:
        raise RuntimeError('Dump differs from supported baseline; no patch applied')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['doctor','baseline','test-host','inspect-dump'])
    parser.add_argument('--dump', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'inspect-dump':
            if args.dump is None and os.environ.get('DUMP'):
                args.dump = Path(os.environ['DUMP'])
            if args.dump is None:
                parser.error('inspect-dump requires an explicitly supplied --dump path or DUMP environment value')
            inspect_dump(args.dump)
        else:
            {'doctor':doctor,'baseline':baseline,'test-host':test_host}[args.action]()
    except (RuntimeError, OSError) as exc:
        sys.exit(str(exc))
