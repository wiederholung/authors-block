"""Integration tests against the real Quarto/Pandoc DOCX writer, stdlib only."""
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from xml.etree import ElementTree as E
import subprocess, shutil

ROOT=Path(__file__).resolve().parents[1]
QUARTO=shutil.which("quarto")
if not QUARTO: raise SystemExit("Quarto is required")
NS={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp":"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a":"http://schemas.openxmlformats.org/drawingml/2006/main",
    "asvg":"http://schemas.microsoft.com/office/drawing/2016/SVG/main",
    "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

def run(args,cwd,success=True):
    p=subprocess.run([QUARTO,*args],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
    if success and p.returncode: raise AssertionError(p.stdout)
    return p

def inherited_reference(path):
    """A nonstandard Author style id and an inherited note size exercise both lookups."""
    raw=subprocess.check_output([QUARTO,"pandoc","--print-default-data-file","reference.docx"])
    w="{"+NS["w"]+"}"
    with ZipFile(BytesIO(raw)) as source, ZipFile(path,"w",ZIP_DEFLATED) as dest:
        for part in source.namelist():
            data=source.read(part)
            if part=="word/styles.xml":
                styles=E.fromstring(data)
                for name,points in [("Author",14),("Affiliation",11)]:
                    old=next((s for s in styles.findall("w:style",NS)
                              if s.get(w+"styleId")==name),None)
                    if old is not None: styles.remove(old)
                    base=E.SubElement(styles,w+"style",{w+"type":"paragraph",w+"styleId":name+"Base"})
                    E.SubElement(base,w+"name",{w+"val":name+" Base"})
                    E.SubElement(E.SubElement(base,w+"rPr"),w+"sz",{w+"val":str(2*points)})
                    s=E.SubElement(styles,w+"style",{w+"type":"paragraph",w+"styleId":name+"Local"})
                    E.SubElement(s,w+"name",{w+"val":name})
                    E.SubElement(s,w+"basedOn",{w+"val":name+"Base"})
                data=E.tostring(styles,encoding="utf-8",xml_declaration=True)
            dest.writestr(part,data)

with TemporaryDirectory(prefix="authors-block-check-") as temp:
    target=Path(temp)
    run(["add",str(ROOT),"--no-prompt"],target)
    inherited_reference(target/"inherited.docx")
    cases={
      "structured":'''lang: zh-Hans
date: 2026-01-02
date-format: YYYY-MM-DD
abstract: Abstract remains present.
author:
  - name: {given: Josiah, family: Carberry}
    orcid: https://orcid.org/0000-0002-1825-0097
    corresponding: true
    email: example@example.org
    equal-contributor: true
    affiliations: [{ref: two}, {ref: one}]
  - name: 陈明
    corresponding: true
    email: second@example.org
    equal-contributor: true
    affiliations: [{ref: two}]
affiliations:
  - {id: one, name: First institution}
  - {id: two, name: Second institution}
''',
      "without_affiliations":'''authors:
  - name: Josiah Carberry
    orcid: 0000-0002-1825-0097
    equal-contributor: true
''',
      "without_orcid":'''author:
  - name: Plain Author
''',
      "without_author":"",
      "correspondence_without_email":'''author:
  - name: Contact Author
    corresponding: true
''',
      "custom_sizes":'''authors-block:
  docx: {author-size: 14, note-size: 11}
author:
  - name: Josiah Carberry
    orcid: 0000-0002-1825-0097
    affiliations: [{ref: one}]
affiliations:
  - {id: one, name: First institution}
''',
      "bookmark_collision":'''author:
  - name: Plain Author
    equal-contributor: true
    affiliations: [{ref: one}]
affiliations:
  - {id: one, name: First institution}
''',
      "invalid":'''author:
  - name: Invalid ID
    orcid: 0000-0002-1825-0098
''',
      "invalid_syntax":'''author:
  - name: Invalid ID
    orcid: not-an-id
'''}
    cases["inherited_sizes"]="author:\n"+cases["custom_sizes"].split("author:\n",1)[1]
    # Exercise a consumer's template with the same structured authors as the stock one.
    stock=run(["pandoc","-D","docx"],target).stdout
    start,author_loop=stock.split("$for(author)$",1)
    _,end=author_loop.split("$endfor$",1)
    (target/"header.xml").write_text(start+"$authors-block-header$"+end,encoding="utf-8")
    cases["structured_template"]=cases["structured"]+"authors-block:\n  docx: {placement: template}\n"
    for name,header in cases.items():
        structured=name in ("structured","structured_template")
        source=target/f"{name}.qmd"
        body="Body remains present.\n"
        if name=="bookmark_collision":
            body+="\n## Existing heading {#authors_block_aff_1}\n\n[Existing span]{#authors_block_equal}\n"
        reference="    reference-doc: inherited.docx\n" if name=="inherited_sizes" else ""
        if name=="structured_template":
            reference+="    template: header.xml\n"
        source.write_text("---\ntitle: Author block check\n"+header+"format:\n  docx:\n"+reference+"    filters: [authors-block]\n---\n\n"+body,encoding="utf-8")
        p=run(["render",source.name,"--to","docx"],target,success=not name.startswith("invalid"))
        if name.startswith("invalid"):
            assert p.returncode and "invalid ORCID" in p.stdout,p.stdout
            print(f"PASS {name} rejected")
            continue
        with ZipFile(source.with_suffix(".docx")) as z:
            document=E.fromstring(z.read("word/document.xml"))
            rels=E.fromstring(z.read("word/_rels/document.xml.rels"))
            text="".join(t.text or "" for t in document.findall(".//w:t",NS)).replace('\u00a0',' ').replace('\ufeff','')
            links=[e.get("Target") for e in rels]
            assert "Body remains present." in text
            relationships={e.get("Id"):e.get("Target") for e in rels}
            bookmarks=document.findall('.//w:bookmarkStart',NS)
            bookmark_names=[b.get('{'+NS['w']+'}name') for b in bookmarks]
            bookmark_ids=[b.get('{'+NS['w']+'}id') for b in bookmarks]
            assert len(bookmark_names)==len(set(bookmark_names)),bookmark_names
            assert len(bookmark_ids)==len(set(bookmark_ids)),bookmark_ids
            end_ids=[b.get('{'+NS['w']+'}id') for b in document.findall('.//w:bookmarkEnd',NS)]
            assert sorted(bookmark_ids)==sorted(end_ids),'Bookmark ranges must close'
            targets={b.get('{'+NS['w']+'}name'):''.join(p.itertext()).replace('\u00a0',' ')
                     for p in document.findall('.//w:p',NS) for b in p.findall('.//w:bookmarkStart',NS)}
            internal=[h for h in document.findall('.//w:hyperlink',NS)
                      if h.get('{'+NS['w']+'}anchor','').startswith('authors_block_')]
            expected={'structured':['1','2','†','2','†'], 'without_affiliations':['†'],
                      'custom_sizes':['1'], 'inherited_sizes':['1'], 'bookmark_collision':['1','†']}.get('structured' if structured else name,[])
            assert [''.join(h.itertext()) for h in internal]==expected,(name,expected)
            for h in internal:
                label=''.join(h.itertext()); anchor=h.get('{'+NS['w']+'}anchor')
                assert anchor in targets,(name,anchor)
                destination=('同等贡献' if structured else 'Equal contribution') if label=='†' else ('First institution' if label=='1' else 'Second institution')
                assert targets[anchor]==label+' '+destination,(name,anchor,targets[anchor])
                props=h.find('w:r/w:rPr',NS)
                for prop,value in [('color','000000'),('u','none'),('sz','19' if name in ('custom_sizes','inherited_sizes') else '16')]:
                    assert props.find('w:'+prop,NS).get('{'+NS['w']+'}val')==value
            if name=='bookmark_collision':
                assert all(h.get('{'+NS['w']+'}anchor').endswith('_2') for h in internal)
            def icon_kind(node):
                svg=node.find('.//asvg:svgBlip',NS)
                if svg is None: return None
                data=z.read('word/'+relationships[svg.get('{'+NS['r']+'}embed')])
                for kind in ('orcid','envelope'):
                    if data==(ROOT/f'_extensions/authors-block/assets/{kind}.svg').read_bytes(): return kind
                raise AssertionError('Unexpected SVG or modified original asset')
            drawings=document.findall('.//w:drawing',NS)
            kinds=[icon_kind(d) for d in drawings]
            if structured or name in ("without_affiliations","custom_sizes","inherited_sizes"):
                assert kinds.count('orcid')==1,kinds
                assert "https://orcid.org/0000-0002-1825-0097" in links
            else:
                assert 'orcid' not in kinds,kinds
                assert not any("orcid.org" in (link or "") for link in links)
            # Neither icon is superscript or a raised text run; the envelope's
            # optical alignment is part of its SVG canvas.
            for word_run in document.findall('.//w:r',NS):
                if word_run.find('.//w:drawing',NS) is not None:
                    assert word_run.find('w:rPr/w:vertAlign',NS) is None
                    assert word_run.find('w:rPr/w:position',NS) is None
                    assert word_run.find('.//asvg:svgBlip',NS) is not None
            if name=="structured_template":
                core=E.fromstring(z.read("docProps/core.xml"))
                creator=core.findtext("{http://purl.org/dc/elements/1.1/}creator")
                assert creator=="Josiah Carberry; 陈明",creator
                assert text.count("Josiah Carberry")==1 and text.count("陈明")==1
            if structured:
                author=next(p for p in document.findall(".//w:p",NS) if p.find(".//asvg:svgBlip",NS) is not None)
                children=list(author)
                image_at=next(i for i,e in enumerate(children) if icon_kind(e)=='orcid')
                marks_at=next(i for i,e in enumerate(children) if e.find('.//w:position',NS) is not None)
                envelope_at=next(i for i,e in enumerate(children) if icon_kind(e)=='envelope')
                assert image_at < marks_at < envelope_at,'Expected name, ORCID, marks, envelope'
                assert ''.join(''.join(e.itertext()) for e in children[marks_at:envelope_at]
                               if e.find('.//w:position',NS) is not None)=='1,2,†'
                assert kinds.count('envelope')==3,kinds
                for word in ("Josiah Carberry","陈明","First institution","Second institution","同等贡献"):
                    assert word in text,(word,text)
                assert '共同第一作者' not in text and '通信作者' not in text and '*' not in text
                contacts=[p for p in document.findall('.//w:p',NS) if 'example@example.org' in ''.join(p.itertext())]
                assert len(contacts)==1
                contact_text=''.join(contacts[0].itertext())
                assert contact_text.index('example@example.org') < contact_text.index('second@example.org')
                assert '; ' in contact_text and 'Josiah' not in contact_text and '陈' not in contact_text
                for email in ('example@example.org','second@example.org'):
                    assert 'mailto:'+email in links
                assert text.index('First institution') < text.index('2026-01-02') < text.index('Abstract remains present.') < text.index('Body remains present.')
            if name=='correspondence_without_email':
                assert kinds==['envelope'] and not any((link or '').startswith('mailto:') for link in links)
            if name in ('custom_sizes','inherited_sizes'):
                extent=drawings[0].find('.//wp:extent',NS)
                assert abs(int(extent.get('cx'))/12700-10.5)<.01,'The effective Author size must scale the ORCID'
                aff=next(p for p in document.findall('.//w:p',NS) if 'First institution' in ''.join(p.itertext()))
                mark=next(r for r in aff.findall('w:r',NS) if ''.join(r.itertext())=='1')
                assert mark.find('w:rPr/w:sz',NS).get('{'+NS['w']+'}val')=='15','The effective Affiliation size must scale its mark'
        print(f"PASS {name}")
print(f"All {len(cases)} DOCX author-block integration cases passed.")
