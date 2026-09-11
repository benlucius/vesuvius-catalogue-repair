"""Optional report builder; requires ReportLab and system DejaVu fonts.

The repair and its tests do not require these PDF-generation dependencies.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import hashlib
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

import repair_catalogue as repair

BASE = Path(__file__).resolve().parent
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
for label, filename in [('Body', 'DejaVuSans.ttf'), ('Strong', 'DejaVuSans-Bold.ttf'), ('Code', 'DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(label, str(FONT_DIR / filename)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Strong')

INK = colors.HexColor('#17313A')
TEAL = colors.HexColor('#126C73')
MUTED = colors.HexColor('#57696F')
LINE = colors.HexColor('#D4DFE0')
PALE = colors.HexColor('#EFF5F4')
AMBER = colors.HexColor('#FFF2D9')
W = A4[0] - 100
styles = {
    'label': ParagraphStyle('label', fontName='Strong', fontSize=9, leading=12, textColor=TEAL, spaceAfter=12),
    'title': ParagraphStyle('title', fontName='Strong', fontSize=25, leading=30, textColor=INK, spaceAfter=13),
    'h': ParagraphStyle('h', fontName='Strong', fontSize=13, leading=18, textColor=INK, spaceBefore=16, spaceAfter=8),
    'body': ParagraphStyle('body', fontName='Body', fontSize=10, leading=14.5, textColor=INK, spaceAfter=9),
    'small': ParagraphStyle('small', fontName='Body', fontSize=8.5, leading=12, textColor=MUTED, spaceAfter=7),
    'cell': ParagraphStyle('cell', fontName='Body', fontSize=8.2, leading=11.8, textColor=INK),
    'head': ParagraphStyle('head', fontName='Strong', fontSize=8.2, leading=11.8, textColor=colors.white),
    'code': ParagraphStyle('code', fontName='Code', fontSize=7.6, leading=11.5, textColor=INK, spaceAfter=7),
}


def p(text, style='body'):
    return Paragraph(text, styles[style])


def link(url, label):
    return '<link href="' + escape(url, {'"': '&quot;'}) + '" color="#126C73"><u>' + escape(label) + '</u></link>'


def table(rows, widths):
    cells = [[p(value, 'head' if i == 0 else 'cell') for value in row] for i, row in enumerate(rows)]
    result = Table(cells, colWidths=widths, hAlign='LEFT', repeatRows=1)
    result.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PALE, colors.white]),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
    ]))
    return result


def note(text, background=PALE):
    result = Table([[p(text, 'body')]], colWidths=[W], hAlign='LEFT')
    result.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), background),
                               ('BOX', (0, 0), (-1, -1), 0.5, LINE),
                               ('LEFTPADDING', (0, 0), (-1, -1), 12),
                               ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                               ('TOPPADDING', (0, 0), (-1, -1), 10),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    return result


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(44, 43, A4[0] - 44, 43)
    canvas.setFont('Body', 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(44, 29, 'Vesuvius catalogue repair | Technical review package | 10 September 2026')
    canvas.drawRightString(A4[0] - 44, 29, str(doc.page))
    canvas.restoreState()


def build():
    manifest = repair.read_json(BASE / 'evidence/manifest.json')
    source = manifest['sources']['metadata.original.json']
    six = repair.read_json(BASE / 'validation.six.json')
    seven = repair.read_json(BASE / 'validation.seven.proposed.json')
    story = []
    story += [p('VESUVIUS CHALLENGE / DATA QUALITY', 'label'),
              p('Catalogue metadata<br/>repair package', 'title'),
              p('Issues #1504 and #1516 | Prepared 10 September 2026', 'small'),
              note('<b>6 directly supported corrections + 1 provenance proposal.</b><br/>The default patch applies six corrections. The seventh is supplied separately for maintainer confirmation.'),
              Spacer(1, 13),
              p('The public catalogue still contains four null volume shapes and three unresolved parent references in the reported records. This package supplies guarded patches, corrected local snapshots and reproducible checks on the actual published metadata.'),
              p('Four verified volume shapes', 'h')]
    rows = [['Sample / volume', 'Before', 'After: level-0 array shape', 'Source']]
    for i, row in enumerate(six['after']['shapes'], 1):
        filename = repair.shape_file(row['sample'], row['volume'])
        rows.append([row['sample'] + '<br/>' + row['volume'], 'null',
                     escape(str(row['array_shape'])), link(manifest['sources'][filename]['url'], 'Zarr ' + str(i))])
    story += [table(rows, [139, 60, 231, W - 430]),
              Spacer(1, 8),
              p('Dimensions are copied directly from each corresponding <font name="Code">0/.zarray</font>, in its published order. They are not inferred from segment coverage bounds. Array contents and resolution are unchanged.', 'small'),
              p('Observed catalogue-consumer result', 'h'),
              table([['Check on selected records', 'Original', 'Six corrections', 'With proposal'],
                     ['Shapes matching array metadata', '0 / 4', '4 / 4', '4 / 4'],
                     ['Typed parent references resolving', '0 / 3', '2 / 3', '3 / 3']],
                    [226, 72, 104, W - 402]),
              Spacer(1, 9),
              p('The snapshot contains 71 volumes; all four null volume shapes are filled. These measurements demonstrate metadata consistency, not improved ink detection, segmentation or recovered text.', 'small'),
              p('Original reports: ' + link('https://github.com/ScrollPrize/villa/issues/1504', '#1504') + ' and ' + link('https://github.com/ScrollPrize/villa/issues/1516', '#1516') + ' by @nerln. Issue #1516 also credits @Bullo27 with independent shape checks. This package does not claim discovery of those defects.', 'small'),
              PageBreak()]

    story += [p('REFERENCE INTEGRITY', 'label'), p('Two corrections.<br/>One explicit decision.', 'title'),
              p('Two volume references have scan IDs in a field typed as a volume. Each ID is present in the same sample\'s scans, absent from its volumes, and agrees with the source volume\'s own <font name="Code">scan_id</font>.'),
              table([['PHerc0009B record', 'Before', 'Direct correction'],
                     ['Volume<br/>20250521125136', 'volume<br/>20250509053741', 'scan<br/>20250509053741'],
                     ['Volume<br/>20250820154339', 'volume<br/>20250718080859', 'scan<br/>20250718080859']], [170, 169, W - 339]),
              p('Segment 20250910185200: proposed parent', 'h'),
              note('Keep <b>type = volume</b> and change the parent ID from <b>20250718080859</b> to <b>20250820154339</b>. This uses the segment\'s declared original volume. <b>Maintainer confirmation is required.</b>', AMBER),
              Spacer(1, 12),
              p('The segment already declares <font name="Code">original_volume_id = 20250820154339</font>. That volume exists and declares scan <font name="Code">20250718080859</font>, which is the segment\'s currently unresolved parent ID. All 311 segments in this snapshot use volume-typed parents.'),
              p('This supports a volume-ID correction rather than merely changing the segment\'s type to scan. It is still an inference about intended provenance: referential consistency alone does not prove the historical processing chain. The six-correction output therefore leaves this segment unchanged.'),
              p('Exact scope and safeguards', 'h'),
              p('The direct variant changes four <font name="Code">properties.shape</font> values and two <font name="Code">creation.derived_from.type</font> values. The proposed variant additionally changes the segment\'s <font name="Code">creation.derived_from.id</font>. Its <font name="Code">original_volume_id</font> is preserved.'),
              p('The utility checks record identities, data paths, captured evidence hashes, current values and scan relationships. Conflicts abort before output is written. Existing outputs are not overwritten. The segment change is enabled only by <font name="Code">--include-segment-proposal</font>.'),
              p('Integration: review the changes, update the authoritative metadata records or export process, and regenerate the catalogue. A patched local snapshot is not a deployed fix and can be superseded by a later upstream export.', 'small'),
              PageBreak()]

    story += [p('REPRODUCIBILITY / HANDOFF', 'label'), p('Evidence and verification', 'title'),
              p('Twelve regression tests passed on the complete captured public catalogue. Both variants passed whole-document comparison and repeat-application checks. The JSON patches were also applied by an independent test interpreter and matched the generated outputs.'),
              table([['Verified property', 'Six corrections', 'With segment proposal'],
                     ['Changed semantic paths', str(six['semantic_change_count']), str(seven['semantic_change_count'])],
                     ['Unrelated semantic changes', '0', '0'],
                     ['Changes on a second application', '0', '0']], [245, 119, W - 364]),
              p('Captured source', 'h'),
              p(link(source['url'], 'Official metadata.json') + '<br/>Retrieved: ' + escape(source['retrieved_utc']) + '<br/>Last-Modified: ' + escape(source['last_modified']) + '<br/>Decoded payload: ' + format(source['decoded_bytes'], ',') + ' bytes', 'small'),
              p('Decoded source SHA-256:<br/>' + source['decoded_sha256'], 'code'),
              p('The manifest records the separate HTTP-response hash, gzip encoding, headers and timestamps. Four original Zarr metadata responses are included. No CT chunks were fetched and no model was trained or run.', 'small'),
              p('Reproduce from the extracted directory', 'h'),
              p('python3 repair_catalogue.py verify<br/>&nbsp;&nbsp;--catalogue evidence/metadata.original.json<br/>&nbsp;&nbsp;--after metadata.six.corrected.json<br/><br/>python3 -m unittest -v test_repair', 'code'),
              p('The first command is shown wrapped for readability; enter it on one line. Python 3.9+ is sufficient for the utility and tests. See README.md for complete commands and verification.log for the actual execution record.', 'small'),
              p('Contribution, review and limits', 'h'),
              p('The added contribution is a guarded repair, fresh evidence and a reproducible handoff for previously reported defects. Code, tests and documentation were prepared with OpenAI Codex at the submitter\'s request. No personal hands-on VC3D use, maintainer acceptance or community adoption is claimed.'),
              p('Original code is offered under MIT; source data keep their existing licences and attribution. A short email for technical review is included. This is a small maintenance contribution with no assigned bounty or guaranteed award.', 'small'),
              p('Project references: ' + link('https://scrollprize.org/faq', 'official contact') + ' | ' + link('https://scrollprize.org/prizes#progress-prizes', 'Progress Prize rules') + ' | ' + link('https://github.com/ScrollPrize/villa/blob/main/CONTRIBUTING.md', 'contribution guidelines') + '.', 'small')]
    output = BASE / 'Catalogue_Repair_Report.pdf'
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=44, leftMargin=44,
                            topMargin=43, bottomMargin=57, title='Vesuvius catalogue metadata repair',
                            author='Catalogue repair submission', subject='Six verified corrections and one provenance proposal',
                            pageCompression=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == '__main__':
    build()
