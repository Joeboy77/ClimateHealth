"""Build the ClimaHealth Predict pitch deck.

Regenerate after editing:  uv run python deck/build_deck.py

White background, two colours, one serif for figures. The deck is built in code so
the numbers on the slides come from one place and can be corrected in one place.
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

DECK = Path(__file__).resolve().parent
SHOTS = DECK / "screenshots"
OUTPUT = DECK / "ClimaHealth-Predict.pptx"

WIDTH, HEIGHT = Inches(13.333), Inches(7.5)

INK = RGBColor(0x1A, 0x1D, 0x1B)
MUTED = RGBColor(0x6F, 0x6D, 0x66)
FAINT = RGBColor(0xA8, 0xA5, 0x9E)
ACCENT = RGBColor(0x0E, 0x6E, 0x63)
ALARM = RGBColor(0xA3, 0x21, 0x18)
RULE = RGBColor(0xE4, 0xE2, 0xDC)

DISPLAY = "Georgia"
BODY = "Helvetica Neue"

MARGIN = Inches(0.85)
CONTENT_WIDTH = WIDTH - MARGIN * 2


def text_box(slide, left, top, width, height, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    frame.paragraphs[0].alignment = align
    return frame


def write(
    frame,
    text,
    size,
    colour=INK,
    font=BODY,
    bold=False,
    space_after=0,
    line=None,
    spacing=None,
    first=False,
):
    paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
    paragraph.space_after = Pt(space_after)
    if line is not None:
        paragraph.line_spacing = line
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = colour
    run.font.name = font
    run.font.bold = bold
    if spacing is not None:
        run.font._rPr.set("spc", str(int(spacing * 100)))
    return paragraph


def blank(presentation):
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    background = slide.background
    background.fill.solid()
    background.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    return slide


def hairline(slide, top, left=MARGIN, width=CONTENT_WIDTH):
    line = slide.shapes.add_shape(1, left, top, width, Emu(9525))
    line.fill.solid()
    line.fill.fore_color.rgb = RULE
    line.line.fill.background()
    line.shadow.inherit = False
    return line


def eyebrow(slide, text, top=Inches(0.62)):
    frame = text_box(slide, MARGIN, top, CONTENT_WIDTH, Inches(0.3))
    write(frame, text.upper(), 11, MUTED, BODY, True, spacing=1.6, first=True)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text.strip()


def picture(slide, name, top, height):
    """Sized by height and centred, so a wide screenshot never runs off the bottom of
    the slide. A missing file leaves a labelled frame, so the gap is obvious rather
    than silently absent."""
    path = SHOTS / name
    if path.exists():
        added = slide.shapes.add_picture(str(path), Emu(0), top, height=height)
        added.left = Emu(int((WIDTH - added.width) / 2))
        outline = slide.shapes.add_shape(1, added.left, top, added.width, height)
        outline.fill.background()
        outline.line.color.rgb = RULE
        outline.shadow.inherit = False
        return added

    width = Inches(height.inches * 1.6)
    left = Emu(int((WIDTH - width) / 2))
    frame_shape = slide.shapes.add_shape(1, left, top, width, height)
    frame_shape.fill.solid()
    frame_shape.fill.fore_color.rgb = RGBColor(0xF5, 0xF4, 0xF1)
    frame_shape.line.color.rgb = RULE
    frame_shape.shadow.inherit = False
    label = frame_shape.text_frame
    label.word_wrap = True
    label.vertical_anchor = MSO_ANCHOR.MIDDLE
    write(label, f"[ drop in: {name} ]", 13, FAINT, BODY, True, first=True)
    label.paragraphs[0].alignment = PP_ALIGN.CENTER
    return frame_shape


def title_slide(presentation):
    slide = blank(presentation)
    frame = text_box(slide, MARGIN, Inches(2.2), CONTENT_WIDTH, Inches(2.6))
    write(frame, "CLIMAHEALTH PREDICT", 12, ACCENT, BODY, True, 18, spacing=2.2, first=True)
    write(frame, "Ghana knows the weather.", 46, INK, DISPLAY, False, 2, line=1.05)
    write(frame, "It does not yet know what the weather", 46, INK, DISPLAY, False, 2, line=1.05)
    write(frame, "is about to do to people.", 46, ACCENT, DISPLAY, False, 20, line=1.05)

    hairline(slide, Inches(5.35))
    footer = text_box(slide, MARGIN, Inches(5.6), CONTENT_WIDTH, Inches(0.9))
    write(
        footer,
        "A climate-health early-warning platform: it turns today's climate into a ranked, "
        "explained health warning for the weeks ahead.",
        15,
        MUTED,
        BODY,
        False,
        6,
        first=True,
    )
    write(footer, "GreenRes Hackathon 2026", 12, FAINT, BODY, True, spacing=1.4)
    notes(
        slide,
        "Open with the one sentence. Do not read the subtitle. "
        "Say: every agency here already has weather data. Nobody turns it into who "
        "gets sick, where, and when. That gap is the whole product.",
    )
    return slide


def problem_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "The gap")

    frame = text_box(slide, MARGIN, Inches(1.15), Inches(6.4), Inches(3.4))
    write(frame, "Cases arrive weeks", 38, INK, DISPLAY, False, 2, line=1.08, first=True)
    write(frame, "after the rain that", 38, INK, DISPLAY, False, 2, line=1.08)
    write(frame, "caused them.", 38, ALARM, DISPLAY, False, 18, line=1.08)
    write(
        frame,
        "That delay is not a problem. It is the opportunity. It is the only "
        "window in which a district can still act before people fall ill.",
        16,
        MUTED,
        BODY,
        False,
        0,
        line=1.45,
    )

    lags = [
        ("Malaria", "2 to 6 weeks", "after rainfall and standing water"),
        ("Cholera", "1 to 3 weeks", "after flooding and unsafe water"),
        ("Meningitis", "2 to 8 weeks", "after dry, dusty harmattan air"),
    ]
    top = Inches(1.35)
    for condition, window, cause in lags:
        row = text_box(slide, Inches(7.5), top, Inches(5.0), Inches(1.1))
        write(row, condition.upper(), 11, MUTED, BODY, True, 4, spacing=1.6, first=True)
        write(row, window, 26, ACCENT, DISPLAY, False, 2)
        write(row, cause, 13, MUTED, BODY)
        top += Inches(1.25)

    hairline(slide, Inches(5.9))
    closing = text_box(slide, MARGIN, Inches(6.1), CONTENT_WIDTH, Inches(0.6))
    write(
        closing,
        "Today Ghana reacts when the cases appear. The information to act earlier already exists.",
        15,
        INK,
        BODY,
        False,
        first=True,
    )
    notes(
        slide,
        "Land the lag window. This is the single idea the whole system rests on. "
        "Say the numbers out loud: two to six weeks for malaria. That is how much "
        "warning we can give.",
    )
    return slide


def engine_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "How it decides")

    frame = text_box(slide, MARGIN, Inches(1.15), Inches(11.6), Inches(1.4))
    write(frame, "The brain is a rules engine, not a guess.", 34, INK, DISPLAY, False, 10, first=True)
    write(
        frame,
        "Published epidemiological thresholds, evaluated the same way every time. "
        "Same inputs, same output. Every warning can name the conditions that caused it.",
        16,
        MUTED,
        BODY,
        False,
        0,
        line=1.45,
    )

    steps = [
        ("Open-Meteo", "live climate for all 260 districts"),
        ("Features", "7-day rain, humidity, heat, dust"),
        ("Pathways", "one per disease, weighted triggers"),
        ("Ranked risk", "level, score, lag window, reasons"),
    ]
    left = MARGIN
    box_width = Inches(2.85)
    for index, (name, detail) in enumerate(steps):
        column = text_box(slide, left, Inches(3.15), box_width, Inches(1.5))
        write(column, f"0{index + 1}", 13, ACCENT, DISPLAY, True, 6, first=True)
        write(column, name, 17, INK, BODY, True, 4)
        write(column, detail, 13, MUTED, BODY, False, 0, line=1.35)
        if index < len(steps) - 1:
            arrow = text_box(slide, left + box_width, Inches(3.2), Inches(0.4), Inches(0.4))
            write(arrow, "→", 16, FAINT, BODY, False, first=True)
        left += Inches(3.05)

    hairline(slide, Inches(5.15))
    frame = text_box(slide, MARGIN, Inches(5.4), CONTENT_WIDTH, Inches(1.4))
    write(
        frame,
        "AI never decides risk. It only phrases what the engine already decided, "
        "in English or Twi.",
        17,
        INK,
        BODY,
        True,
        8,
        first=True,
    )
    write(
        frame,
        "This is what makes the system defensible to a health ministry: an officer can "
        "ask why a district was flagged and get the exact thresholds back, not a "
        "model's opinion.",
        15,
        MUTED,
        BODY,
        False,
        0,
        line=1.45,
    )
    notes(
        slide,
        "This is your credibility slide. Judges asked whether the prediction is real. "
        "Answer: deterministic rules from published thresholds, reproducible, "
        "explainable. The AI is a translator, not a decider. Say that sentence exactly.",
    )
    return slide


def screenshot_slide(presentation, eyebrow_text, headline, blurb, image, note, caption=None):
    slide = blank(presentation)
    eyebrow(slide, eyebrow_text)

    frame = text_box(slide, MARGIN, Inches(1.1), Inches(11.6), Inches(1.0))
    write(frame, headline, 30, INK, DISPLAY, False, 8, first=True)
    write(frame, blurb, 15, MUTED, BODY, False, 0, line=1.4)

    picture(slide, image, Inches(2.15), Inches(4.55))

    if caption is not None:
        caption_frame = text_box(slide, MARGIN, Inches(6.85), CONTENT_WIDTH, Inches(0.4))
        write(caption_frame, caption, 12, FAINT, BODY, False, first=True)
        caption_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    notes(slide, note)
    return slide


def loop_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "Institutional integration")

    frame = text_box(slide, MARGIN, Inches(1.1), Inches(11.6), Inches(1.0))
    write(frame, "A report is a claim until somebody goes and looks.", 30, INK, DISPLAY, False, 8, first=True)
    write(
        frame,
        "Ɔhwɛfoɔ is an on-ground officer role in the platform. Validation and repair are "
        "different jobs held by different people, and neither can take the other's step.",
        15,
        MUTED,
        BODY,
        False,
        0,
        line=1.4,
    )

    stages = [
        ("Citizen reports", "photo, location, note", "Dawuro app"),
        ("Ɔhwɛfoɔ validates", "goes to the site, confirms", "25% → 50%"),
        ("Agency works", "GHS, NADMO, EPA, Assembly", "50% → 75%"),
        ("Resolved", "closed with what was done", "100%"),
    ]
    left = MARGIN
    for index, (name, detail, meta) in enumerate(stages):
        column = text_box(slide, left, Inches(2.9), Inches(2.9), Inches(1.8))
        write(column, f"0{index + 1}", 13, ACCENT, DISPLAY, True, 6, first=True)
        write(column, name, 17, INK, BODY, True, 4)
        write(column, detail, 13, MUTED, BODY, False, 6, line=1.35)
        write(column, meta, 12, ACCENT, BODY, True)
        left += Inches(3.05)

    hairline(slide, Inches(5.0))
    frame = text_box(slide, MARGIN, Inches(5.25), CONTENT_WIDTH, Inches(1.5))
    write(
        frame,
        "Every step is written down: who moved it, when, and what they found.",
        17,
        INK,
        BODY,
        True,
        8,
        first=True,
    )
    write(
        frame,
        "The person who filed the report watches the same bar the officers do. Reporting "
        "a hazard into a form that never answers is how people learn not to bother.",
        15,
        MUTED,
        BODY,
        False,
        0,
        line=1.45,
    )
    notes(
        slide,
        "Judges said institutional integration was unproven. This is the answer: a named "
        "role, a permission model, an append-only trail, and the citizen sees it close. "
        "Say: the agencies do not have to trust the app, they have to trust their own officer.",
    )
    return slide


def mobile_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "In the hand")

    frame = text_box(slide, MARGIN, Inches(1.05), Inches(11.6), Inches(1.0))
    write(frame, "Dawuro: the warning, the weather, and the reason.", 30, INK, DISPLAY, False, 8, first=True)
    write(
        frame,
        "Named after the gong-gong that has carried public warnings in Ghana for "
        "centuries. English and Twi, read aloud for anybody who cannot read the screen.",
        15,
        MUTED,
        BODY,
        False,
        0,
        line=1.4,
    )

    shots = [
        ("m1-home.png", "Today's warning, with the conditions behind it"),
        ("m2-quiz.png", "The daily run: points, streak, and why"),
        ("m3-report.png", "What you reported, and how far it has got"),
    ]
    left = Inches(1.35)
    for name, caption in shots:
        path = SHOTS / name
        height = Inches(4.0)
        if path.exists():
            added = slide.shapes.add_picture(str(path), left, Inches(2.35), height=height)
            added.left = left + Emu(int((Inches(3.3) - added.width) / 2))
        else:
            frame_shape = slide.shapes.add_shape(1, left + Inches(0.6), Inches(2.35), Inches(2.1), height)
            frame_shape.fill.solid()
            frame_shape.fill.fore_color.rgb = RGBColor(0xF5, 0xF4, 0xF1)
            frame_shape.line.color.rgb = RULE
            frame_shape.shadow.inherit = False
            label = frame_shape.text_frame
            label.word_wrap = True
            label.vertical_anchor = MSO_ANCHOR.MIDDLE
            write(label, f"[ {name} ]", 12, FAINT, BODY, True, first=True)
            label.paragraphs[0].alignment = PP_ALIGN.CENTER

        caption_frame = text_box(slide, left, Inches(6.5), Inches(3.3), Inches(0.6))
        write(caption_frame, caption, 12, MUTED, BODY, False, first=True)
        caption_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        left += Inches(3.6)

    notes(
        slide,
        "Keep this short: fifteen seconds. The app is the reach story, not the "
        "technical one. If time is tight, this is the slide to cut.",
    )
    return slide


def reward_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "Reward feasibility")

    frame = text_box(slide, MARGIN, Inches(1.1), Inches(6.5), Inches(3.6))
    write(frame, "Points buy health cover,", 32, INK, DISPLAY, False, 2, line=1.08, first=True)
    write(frame, "not cash.", 32, ACCENT, DISPLAY, False, 16, line=1.08)
    write(
        frame,
        "3,500 points is one year of NHIS cover. The number is derived, not chosen: "
        "the adult premium is about GHS 35, and the platform values a point at one "
        "pesewa.",
        16,
        MUTED,
        BODY,
        False,
        14,
        line=1.45,
    )
    write(
        frame,
        "No money leaves the platform. No float to hold, no payout licence, "
        "no transfer that cannot be recalled.",
        16,
        INK,
        BODY,
        True,
        0,
        line=1.45,
    )

    facts = [
        ("3,500", "points for a year of cover"),
        ("~35 days", "of daily use to earn it"),
        ("0", "cedis of platform liability"),
    ]
    top = Inches(1.3)
    for value, label in facts:
        row = text_box(slide, Inches(7.7), top, Inches(4.8), Inches(1.1))
        write(row, value, 34, ACCENT, DISPLAY, False, 2, first=True)
        write(row, label, 14, MUTED, BODY)
        top += Inches(1.3)

    hairline(slide, Inches(5.35))
    frame = text_box(slide, MARGIN, Inches(5.6), CONTENT_WIDTH, Inches(1.2))
    write(
        frame,
        "The platform never says a renewal happened.",
        17,
        INK,
        BODY,
        True,
        8,
        first=True,
    )
    write(
        frame,
        "It records who earned one and hands that to Ghana Health Service, who renew and "
        "confirm. Claiming otherwise would be the platform speaking for a government scheme.",
        15,
        MUTED,
        BODY,
        False,
        0,
        line=1.45,
    )
    notes(
        slide,
        "Judges questioned reward feasibility directly. This slide is the rebuttal. "
        "Emphasise: we removed the cash payout entirely. There is nothing to fund and "
        "nothing to regulate. GHS already collects these premiums.",
    )
    return slide


def reach_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "Reach")

    frame = text_box(slide, MARGIN, Inches(1.1), Inches(11.6), Inches(1.0))
    write(frame, "A smartphone is not a requirement.", 32, INK, DISPLAY, False, 8, first=True)
    write(
        frame,
        "The people most exposed to climate-driven illness are the least likely to own "
        "one. Three front doors, one engine behind all of them.",
        16,
        MUTED,
        BODY,
        False,
        0,
        line=1.4,
    )

    doors = [
        (
            "Dawuro app",
            "Android and iOS",
            "Forecast, weather, daily quiz, hazard reporting with photo, "
            "progress on what you reported. English and Twi, read aloud.",
        ),
        (
            "USSD",
            "Africa's Talking",
            "Any feature phone, no data, no app. Dial the shortcode, choose "
            "language and district, get today's warning.",
        ),
        (
            "SMS",
            "Moolre",
            "Push warnings to a district when risk crosses the threshold, "
            "for people who never open anything.",
        ),
    ]
    left = MARGIN
    for name, provider, detail in doors:
        column = text_box(slide, left, Inches(2.9), Inches(3.6), Inches(2.6))
        write(column, name, 22, INK, DISPLAY, False, 4, first=True)
        write(column, provider.upper(), 11, ACCENT, BODY, True, 10, spacing=1.4)
        write(column, detail, 14, MUTED, BODY, False, 0, line=1.45)
        left += Inches(3.9)

    hairline(slide, Inches(5.8))
    frame = text_box(slide, MARGIN, Inches(6.0), CONTENT_WIDTH, Inches(0.6))
    write(
        frame,
        "USSD is built and answering: dial, choose English, choose region, choose district, "
        "get the warning.",
        15,
        INK,
        BODY,
        False,
        first=True,
    )
    notes(
        slide,
        "Judges flagged USSD and SMS as not implemented. USSD now runs on Africa's "
        "Talking and answers a full dial-through. If asked, offer to show the "
        "terminal transcript in the backup slide.",
    )
    return slide


def answers_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "What you asked us last time")

    frame = text_box(slide, MARGIN, Inches(1.05), Inches(11.6), Inches(0.7))
    write(frame, "Three criticisms, three answers.", 32, INK, DISPLAY, False, 0, first=True)

    rows = [
        (
            "Field validation unproven",
            "Ɔhwɛfoɔ role: an officer stands where the report was filed and "
            "confirms it before any agency spends a truck. Every validation is signed and timestamped.",
        ),
        (
            "Institutional integration unproven",
            "Reports move through named agency stages with a permission model. "
            "Role-scoped views for GHS, EPA, GMet, NADMO and the District Assembly.",
        ),
        (
            "Reward feasibility unproven",
            "Cash removed. Points buy NHIS cover at a rate derived from the real premium, "
            "issued by Ghana Health Service, not by us.",
        ),
    ]
    top = Inches(2.0)
    for criticism, answer in rows:
        hairline(slide, top - Inches(0.22))
        row = text_box(slide, MARGIN, top, Inches(4.2), Inches(1.2))
        write(row, criticism, 17, ALARM, BODY, True, 0, line=1.3, first=True)
        response = text_box(slide, Inches(5.5), top, Inches(7.0), Inches(1.2))
        write(response, answer, 15, INK, BODY, False, 0, line=1.45, first=True)
        top += Inches(1.55)

    notes(
        slide,
        "This is the slide that wins or loses it. Say the criticism out loud before "
        "the answer. Judges remember being listened to. Do not rush this one.",
    )
    return slide


def close_slide(presentation):
    slide = blank(presentation)

    frame = text_box(slide, MARGIN, Inches(2.0), Inches(11.6), Inches(2.6))
    write(frame, "CLIMAHEALTH PREDICT", 12, ACCENT, BODY, True, 20, spacing=2.2, first=True)
    write(frame, "The climate signal is already there.", 36, INK, DISPLAY, False, 2, line=1.1)
    write(frame, "We turn it into a warning", 36, INK, DISPLAY, False, 2, line=1.1)
    write(frame, "somebody can act on.", 36, ACCENT, DISPLAY, False, 0, line=1.1)

    hairline(slide, Inches(5.0))
    facts = [
        ("260", "districts, live"),
        ("5", "disease pathways"),
        ("963", "tests passing"),
    ]
    left = MARGIN
    for value, label in facts:
        column = text_box(slide, left, Inches(5.3), Inches(3.4), Inches(1.0))
        write(column, value, 30, ACCENT, DISPLAY, False, 2, first=True)
        write(column, label, 13, MUTED, BODY)
        left += Inches(3.9)

    notes(
        slide,
        "Close on the one line, then stop talking. Let the numbers sit. "
        "Have the backup slides ready for Q&A.",
    )
    return slide


def backup_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "Backup · for questions")

    frame = text_box(slide, MARGIN, Inches(1.05), Inches(11.6), Inches(0.7))
    write(frame, "How it is built.", 30, INK, DISPLAY, False, 0, first=True)

    columns = [
        (
            "Architecture",
            "Pure rules engine with no framework, no I/O, no AI. Services depend on "
            "interfaces. An automated test fails the build if a layer imports upward.",
        ),
        (
            "Data",
            "Open-Meteo for all 260 districts, fetched concurrently and cached in Postgres. "
            "Photos in Cloudinary. Reports, stages and timelines persisted.",
        ),
        (
            "Honesty",
            "Twi wording is composed, never machine-translated, and carries a provenance "
            "field. Voice never reads a language the phone has no voice for.",
        ),
    ]
    left = MARGIN
    for name, detail in columns:
        column = text_box(slide, left, Inches(2.2), Inches(3.6), Inches(2.8))
        write(column, name.upper(), 11, ACCENT, BODY, True, 10, spacing=1.6, first=True)
        write(column, detail, 14, MUTED, BODY, False, 0, line=1.5)
        left += Inches(3.9)

    hairline(slide, Inches(5.2))
    frame = text_box(slide, MARGIN, Inches(5.45), CONTENT_WIDTH, Inches(1.4))
    write(frame, "Known limits, stated plainly.", 16, INK, BODY, True, 8, first=True)
    write(
        frame,
        "The engine has not yet been backtested against DHIMS2 case data. That is the "
        "next piece of work, and it is the one that turns a defensible model into a "
        "validated one.",
        14,
        MUTED,
        BODY,
        False,
        0,
        line=1.45,
    )
    notes(
        slide,
        "Only show if asked. Volunteering the DHIMS2 gap before being asked reads as "
        "confident; being caught without it reads as careless.",
    )
    return slide


def build() -> Path:
    presentation = Presentation()
    presentation.slide_width, presentation.slide_height = WIDTH, HEIGHT

    title_slide(presentation)
    problem_slide(presentation)
    engine_slide(presentation)
    screenshot_slide(
        presentation,
        "The national picture",
        "51 of 260 districts are at high risk or above, today.",
        "Every district evaluated against every pathway, ranked, and explained. "
        "This is live output, not a mock.",
        "w1-national.png",
        "Point at the figure, then the map, then the ranked list. Say: this is running "
        "against live Open-Meteo data for all 260 districts right now.",
        "ClimaHealth Predict · Agency Command Platform · signed in as Ghana Health Service",
    )
    screenshot_slide(
        presentation,
        "One platform, five mandates",
        "Each agency opens on the layer it is responsible for.",
        "EPA lands on dust and PM10. NADMO on rainfall. GMet on humidity. GHS on health "
        "risk. Same engine, same districts, different question.",
        "w3-epa.png",
        "This answers the note about every agency seeing only health. Say: an air "
        "quality officer should not have to hunt for air quality.",
        "Signed in as Environmental Protection Agency · Dust & PM10 layer active",
    )
    loop_slide(presentation)
    mobile_slide(presentation)
    screenshot_slide(
        presentation,
        "The renewal queue",
        "Ghana Health Service sees who has earned cover, and who is close.",
        "Ranked by points, with the phone number to reach them on. Under-18s are flagged "
        "as already exempt rather than shown a target.",
        "w2-renewals.png",
        "Point at Kofi Mensah: 20 points to go. Say: that is one more day of use. "
        "This is the screen that makes the reward real to an officer.",
        "NHIS renewals · Ghana Health Service only",
    )
    reward_slide(presentation)
    reach_slide(presentation)
    answers_slide(presentation)
    close_slide(presentation)
    backup_slide(presentation)

    presentation.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    path = build()
    print(f"{path}  ({path.stat().st_size / 1024:.0f} KB)")
