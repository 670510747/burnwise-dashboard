"""Run in the existing notebook kernel: %run -i "PATH/export_web_bundle.py""" 
from pathlib import Path
import gzip, hashlib, json, zipfile, shutil, io
import pandas as pd

_template = Path(__file__).resolve().parent
_snapshot = json.loads((_template/'data/burnwise_reviewed4_snapshot.json').read_text(encoding='utf-8'))
if 'master_plots' not in globals():
    raise RuntimeError('Run this file with %run -i from the kernel containing the completed REVIEWED(4) master_plots.')
_master = master_plots.copy()
_expected = {'Burn':3403,'No Burn':38787,'ข้อมูลไม่เพียงพอ':5121}
if len(_master)!=47311 or _master['burn_status'].value_counts().to_dict()!=_expected:
    raise ValueError('Master counts do not match the supplied REVIEWED(4) results. Do not combine runs.')
if _master['plot_id'].isna().any() or _master['plot_id'].duplicated().any():
    raise ValueError('Master has missing or duplicate plot IDs.')
if 'THRESHOLD' not in globals() or abs(float(THRESHOLD)-_snapshot['threshold'])>1e-10:
    raise ValueError('THRESHOLD differs from REVIEWED(4). Use the completed original kernel.')
for _key in ['pre_start','pre_end','post_start','post_end']:
    _target = _key.replace('_end','_end_exclusive') if _key.endswith('_end') else _key
    if _key not in globals() or str(globals()[_key])[:10]!=_snapshot[_target]:
        raise ValueError(f'{_key} differs from REVIEWED(4). Do not mix runs.')
_dest = Path.cwd()/'burnwise_reviewed4_web_export'
_dest.mkdir(exist_ok=True)
for _name in ['app.py','requirements.txt','.gitattributes']:
    shutil.copy2(_template/_name,_dest/_name)
shutil.copytree(_template/'.streamlit',_dest/'.streamlit',dirs_exist_ok=True)
shutil.copytree(_template/'data',_dest/'data',dirs_exist_ok=True)
_payload = _master.to_csv(index=False).encode('utf-8-sig')
_packed = gzip.compress(_payload,compresslevel=9,mtime=0)
assert gzip.decompress(_packed)==_payload
_name = 'burnwise_master_plots_with_measures_last1.csv.gz'
_path = _dest/'data'/_name
_tmp = _path.with_suffix('.tmp'); _tmp.write_bytes(_packed); _tmp.replace(_path)
_verify = pd.read_csv(io.BytesIO(gzip.decompress(_path.read_bytes())),usecols=['plot_id'])
assert len(_verify)==47311 and _verify['plot_id'].is_unique
_manifest = {**_snapshot,'master_available':True,'master_sha256':hashlib.sha256(_packed).hexdigest()}
(_dest/'data/burnwise_run_manifest.json').write_text(json.dumps(_manifest,ensure_ascii=False,indent=2),encoding='utf-8')
_zip_path = _dest.with_suffix('.zip')
with zipfile.ZipFile(_zip_path,'w',zipfile.ZIP_DEFLATED) as _zip:
    for _p in sorted(_dest.rglob('*')):
        if _p.is_file() and '__pycache__' not in _p.parts:
            _zip.write(_p,_p.relative_to(_dest))
with zipfile.ZipFile(_zip_path) as _zip:assert _zip.testzip() is None
print('Export complete:', _zip_path)
print('Master: 47,311 rows; gzip round-trip and hash checked. No Earth Engine request made.')
print('Put the ZIP contents at your GitHub repository root, preserving data/ and .streamlit/.')
