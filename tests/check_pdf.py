"""Real Quarto/XeLaTeX integration, independent of quarto-template."""
from pathlib import Path
from path_fixture import unicode_path_label
import shutil, subprocess, tempfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix=f'authors-block-{unicode_path_label()} pdf-') as folder:
    root = Path(folder)
    shutil.copytree(ROOT / '_extensions', root / '_extensions')
    def render(name, cls='scrartcl', size=11, people=True, invalid=False):
        metadata = '''author:
  - name: "Alpha & Beta_Name"
    orcid: 0000-0002-1825-0097
    affiliations: [{ref: lab}]
    equal-contributor: true
    corresponding: true
    email: a_test@example.org
  - name: "Second Author"
    affiliations: [{ref: lab}]
    equal-contributor: true
affiliations:
  - id: lab
    name: "Research & Development Institute with a long descriptive institutional name"
''' if people else 'author: Solo Author\n'
        if invalid: metadata=metadata.replace('1825-0097','1825-0098')
        qmd=root/f'{name}.qmd'
        qmd.write_text('---\ntitle: Author integration\ndate: 2026-11-17\nabstract: Abstract sentinel.\n'+metadata+f'''format:
  pdf:
    documentclass: {cls}
    fontsize: {size}pt
    pdf-engine: xelatex
    colorlinks: false
    filters: [quarto, authors-block]
---
Body sentinel.
''', encoding='utf-8')
        result=subprocess.run(['quarto','render',qmd.name,'--to','pdf'],cwd=root,
                              capture_output=True,text=True,encoding='utf-8')
        if invalid:
            assert result.returncode and 'invalid ORCID check digit' in result.stdout+result.stderr
            return
        assert result.returncode==0, result.stdout+result.stderr
        reader=PdfReader(qmd.with_suffix('.pdf'))
        text=' '.join(p.extract_text() for p in reader.pages)
        assert 'Body sentinel' in text and 'Abstract sentinel' in text
        assert 'Alpha & Beta_Name' in text if people else 'Solo Author' in text
        assert 'ORCID' not in str(reader.metadata.author)
        if not people: return
        links=[a.get_object() for p in reader.pages for a in p.get('/Annots',[])]
        uris=[str(a.get('/A',{}).get('/URI','')) for a in links]
        assert 'mailto:a_test@example.org' in uris
        icon=next(a for a in links if 'orcid.org' in str(a.get('/A',{})))
        internal=[a.get('/A',{}).get('/D') for a in links if a.get('/A',{}).get('/S')=='/GoTo']
        assert len(internal)>=4
        for a in internal: assert str(a) in reader.named_destinations
        assert text.index('Research &') < text.index('Abstract sentinel')
        return float(icon['/Rect'][3])-float(icon['/Rect'][1])
    small=render('english')
    large=render('large',size=14)
    assert large>small*1.1, (small,large)
    render('chinese',cls='ctexart')
    render('optional',people=False)
    render('invalid',invalid=True)
print('PDF: two classes, font scaling, optional metadata, escaping, links and invalid ORCID passed')
