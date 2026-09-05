"""New short-answer qualification screen, unrelated to language targets; no calls."""
import json
from pathlib import Path
from ainglish.reader_qualification import validate_screen

ROOT=Path(__file__).resolve().parent

def main():
    out=ROOT/'qualification';out.mkdir(exist_ok=True)
    controls=[]
    for i,(a,b,object_) in enumerate([
        ('Tavi','Orin','amber parcel'),('Nora','Fenn','sealed envelope'),
        ('Cora','Seth','blue notebook'),('Ivo','Lara','silver key'),
        ('Runa','Niko','green folder'),('Edda','Milo','violet ticket'),
        ('Ari','Zola','brass token'),('Dara','Kian','white box')]):
        choices=[a,b,'not determined','neither'];choices=choices[i%4:]+choices[:i%4]
        labels=list('ABCD')
        controls.append({'id':f'opaque-qualification-{i}',
            'detectable':f'{a}, not {b}, holds the {object_}.',
            'other':f'Either {a} or {b} holds the {object_}; no holder is specified.',
            'question':f'Who holds the {object_}? Answer using the option letter. '+
                ' '.join(f'{l} = {t}.' for l,t in zip(labels,choices)),
            'options':labels,'answer':labels[choices.index(a)]})
    for model in ['mistral','gemma']:
        previous=json.loads((ROOT.parent/'reader-qualification-local-v1-2026-09-04'/f'{model}-screen.json').read_text())
        # Same existing immutable weights, new response-budget configuration. Do not
        # retroactively extend either aborted mean attempt's admissibility contract.
        previous['reader']['max_tokens']=64
        previous['reader']['seed']=2026090581
        previous['controls']=controls
        previous['validity_days']=7
        validate_screen(previous)
        with (out/f'{model}-screen.json').open('x') as f:json.dump(previous,f,indent=2);f.write('\n')
    print('Two result-free screens frozen; sixteen cells per reader; zero calls.')

if __name__=='__main__':main()
