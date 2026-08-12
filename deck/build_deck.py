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

    frame = text_box(slide, MARGIN, Inches(1.0), Inches(11.6), Inches(0.9))
    write(frame, "Dawuro: the warning, the weather, and the reason.", 28, INK, DISPLAY, False, 6, first=True)
    write(
        frame,
        "Named after the gong-gong that has carried public warnings in Ghana for "
        "centuries. Five languages, read aloud, and a daily lesson that pays.",
        14,
        MUTED,
        BODY,
        False,
        0,
        line=1.4,
    )

    shots = [
        ("m1-home.png", "Today's risk, in plain words"),
        ("m2-quiz.png", "Learn by answering, wrong or right"),
        ("m3-finish.png", "Points and streak, earned daily"),
        ("m4-report.png", "Report a hazard with a photo"),
        ("m5-twi.png", "The same warning in Twi"),
    ]
    left = Inches(0.55)
    slot = Inches(2.5)
    height = Inches(4.2)
    for name, caption in shots:
        path = SHOTS / name
        if path.exists():
            added = slide.shapes.add_picture(str(path), left, Inches(2.15), height=height)
            added.left = left + Emu(int((slot - added.width) / 2))
        else:
            width = Inches(1.95)
            frame_shape = slide.shapes.add_shape(
                1, left + Emu(int((slot - width) / 2)), Inches(2.15), width, height
            )
            frame_shape.fill.solid()
            frame_shape.fill.fore_color.rgb = RGBColor(0xF5, 0xF4, 0xF1)
            frame_shape.line.color.rgb = RULE
            frame_shape.shadow.inherit = False
            label = frame_shape.text_frame
            label.word_wrap = True
            label.vertical_anchor = MSO_ANCHOR.MIDDLE
            write(label, f"[ {name} ]", 10, FAINT, BODY, True, first=True)
            label.paragraphs[0].alignment = PP_ALIGN.CENTER

        caption_frame = text_box(slide, left, Inches(6.55), slot, Inches(0.6))
        write(caption_frame, caption, 11, MUTED, BODY, False, first=True)
        caption_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        left += slot + Inches(0.06)

    notes(
        slide,
        "Fifteen seconds. Point at the Twi screen last and say: this is the same "
        "warning, and the app tells the reader honestly that the wording is awaiting "
        "review by a Twi speaker and that their phone cannot read it aloud yet. "
        "Nobody else in this room will show you a screen admitting its own limits.",
    )
    return slide



def burden_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "The problem")

    frame = text_box(slide, MARGIN, Inches(1.1), Inches(11.6), Inches(0.9))
    write(frame, "Climate-driven disease is Ghana's largest health burden.", 30, INK, DISPLAY, False, 8, first=True)
    write(
        frame,
        "Malaria, cholera, meningitis and heat illness all track the weather. "
        "Every one of them is driven by conditions we can already measure.",
        15,
        MUTED,
        BODY,
        False,
        0,
        line=1.4,
    )

    figures = [
        ("6.7m", "malaria cases in Ghana in 2024", "WHO World Malaria Report 2024"),
        ("11,635", "malaria deaths in that year", "WHO World Malaria Report 2024"),
        ("~196", "cases per 1,000 at risk", "WHO, broadly flat since 2023"),
    ]
    left = MARGIN
    for value, label, source in figures:
        column = text_box(slide, left, Inches(2.6), Inches(3.6), Inches(1.9))
        write(column, value, 44, ALARM, DISPLAY, False, 4, first=True)
        write(column, label, 15, INK, BODY, True, 6, line=1.3)
        write(column, source, 11, FAINT, BODY, False, 0, line=1.3)
        left += Inches(3.9)

    hairline(slide, Inches(4.9))
    frame = text_box(slide, MARGIN, Inches(5.15), CONTENT_WIDTH, Inches(1.6))
    write(
        frame,
        "Ghana is one of the 15 highest-burden countries in the world.",
        17,
        INK,
        BODY,
        True,
        8,
        first=True,
    )
    write(
        frame,
        "The response is reactive: cases are counted after people are already ill. "
        "The climate data that precedes those cases is free, public, and updated daily. "
        "Nobody is turning it into a warning.",
        15,
        MUTED,
        BODY,
        False,
        0,
        line=1.45,
    )
    notes(
        slide,
        "Open the problem with the number, not the adjective. 6.7 million cases, "
        "11,635 deaths, one year, one country. Then the turn: all of it follows weather "
        "we can already see. Source is WHO World Malaria Report 2024, on the sources slide.",
    )
    return slide


def solution_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "Our solution")

    frame = text_box(slide, MARGIN, Inches(1.1), Inches(11.6), Inches(1.5))
    write(frame, "ClimaHealth Predict", 34, INK, DISPLAY, False, 6, first=True)
    write(
        frame,
        "Reads a district's climate today, and says which health risks are rising, why, "
        "how long before cases appear, and who is most affected.",
        17,
        MUTED,
        BODY,
        False,
        0,
        line=1.4,
    )

    parts = [
        (
            "For the public",
            "Dawuro",
            "Daily forecast and weather, a hazard you can report with a photo, "
            "and a daily lesson that pays in NHIS cover.",
        ),
        (
            "For the agencies",
            "Command Platform",
            "260 districts ranked and explained, alerts, an incident room, "
            "readiness, and a view per agency mandate.",
        ),
        (
            "For everyone else",
            "USSD and SMS",
            "The same warning on any feature phone, with no data and no app, "
            "because a smartphone is not a requirement.",
        ),
    ]
    left = MARGIN
    for audience, name, detail in parts:
        column = text_box(slide, left, Inches(3.1), Inches(3.6), Inches(2.6))
        write(column, audience.upper(), 11, MUTED, BODY, True, 6, spacing=1.6, first=True)
        write(column, name, 22, ACCENT, DISPLAY, False, 8)
        write(column, detail, 14, MUTED, BODY, False, 0, line=1.45)
        left += Inches(3.9)

    hairline(slide, Inches(6.0))
    frame = text_box(slide, MARGIN, Inches(6.2), CONTENT_WIDTH, Inches(0.6))
    write(
        frame,
        "One engine behind all three. The prediction is computed once and reaches people "
        "by whatever door they can open.",
        15,
        INK,
        BODY,
        False,
        first=True,
    )
    notes(
        slide,
        "Say the one-liner from the top of the slide and then stop. The three columns "
        "are for the judges to read, not for you to narrate. Point, do not recite.",
    )
    return slide


def accessibility_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "Accessibility")

    frame = text_box(slide, MARGIN, Inches(1.05), Inches(5.3), Inches(3.9))
    write(frame, "Built for the people", 32, INK, DISPLAY, False, 2, line=1.08, first=True)
    write(frame, "most exposed, not the", 32, INK, DISPLAY, False, 2, line=1.08)
    write(frame, "easiest to reach.", 32, ACCENT, DISPLAY, False, 16, line=1.08)
    write(
        frame,
        "The hackathon asks us to reach youth and marginalised groups. Those are the "
        "people least likely to own a smartphone, read fluently, or speak English at "
        "home. Every one of those is designed for, not apologised for.",
        15,
        MUTED,
        BODY,
        False,
        0,
        line=1.5,
    )

    picture_left = Inches(9.55)
    path = SHOTS / "m6-language.png"
    if path.exists():
        slide.shapes.add_picture(str(path), picture_left, Inches(1.2), height=Inches(5.4))

    rows = [
        ("Five languages", "English, Twi, Ga, Ewe, Dagbani, chosen at sign-up"),
        ("Read aloud", "Every forecast, lesson and quiz answer can be spoken"),
        ("Never a wrong voice", "If the phone has no voice for a language, it says so and stays silent"),
        ("Age-banded content", "A nine-year-old and a grandmother get different wording"),
        ("No smartphone needed", "USSD on any handset; SMS for people who open nothing"),
        ("Works offline", "The last forecast is kept; reports queue and send themselves"),
    ]
    top = Inches(1.25)
    for name, detail in rows:
        row = text_box(slide, Inches(6.4), top, Inches(3.0), Inches(0.85))
        write(row, name, 15, ACCENT, BODY, True, 2, first=True)
        write(row, detail, 13, MUTED, BODY, False, 0, line=1.35)
        top += Inches(0.88)

    notes(
        slide,
        "This is the slide that ties you to the hackathon theme. Say: the people most "
        "exposed to climate illness are the least likely to own a smartphone. If the "
        "product only works on a good phone in English, it has missed them. "
        "If asked for proof, go to the Twi screenshot on the app slide.",
    )
    return slide


def sources_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "Sources")

    frame = text_box(slide, MARGIN, Inches(1.05), Inches(11.6), Inches(0.7))
    write(frame, "Where the numbers come from.", 30, INK, DISPLAY, False, 0, first=True)

    rows = [
        (
            "Malaria burden",
            "6.7m cases and 11,635 deaths in Ghana, 2024",
            "WHO, World Malaria Report 2024",
        ),
        (
            "NHIS coverage",
            "18.5m active members, about 56% of the population",
            "National Health Insurance Authority, 2025",
        ),
        (
            "NHIS premium",
            "GHS 7.20 to 48 a year by income band; GHS 30 to 50 informal",
            "NHIA scheme documentation",
        ),
        (
            "Mobile reach",
            "38.3m connections, 110% of population; 69.9% use the internet",
            "GSMA Intelligence / DataReportal, Digital 2025 Ghana",
        ),
        (
            "Climate data",
            "Daily observations and forecast for all 260 districts",
            "Open-Meteo, live in the product",
        ),
        (
            "Behaviour change",
            "Severity, vulnerability and a doable action are all required",
            "Protection Motivation Theory, Rogers 1975; Health Belief Model",
        ),
        (
            "District boundaries",
            "260 district polygons drawn on the map",
            "geoBoundaries, CC BY 4.0",
        ),
    ]
    top = Inches(1.85)
    for topic, claim, source in rows:
        hairline(slide, top - Inches(0.12))
        row = text_box(slide, MARGIN, top, Inches(2.9), Inches(0.62))
        write(row, topic, 13, INK, BODY, True, 0, first=True)
        middle = text_box(slide, Inches(3.9), top, Inches(5.1), Inches(0.62))
        write(middle, claim, 12, MUTED, BODY, False, 0, line=1.3, first=True)
        right = text_box(slide, Inches(9.3), top, Inches(3.3), Inches(0.62))
        write(right, source, 11, ACCENT, BODY, False, 0, line=1.3, first=True)
        top += Inches(0.73)

    notes(
        slide,
        "Do not present this slide. It exists so that when a judge asks where a number "
        "came from, you turn to it and answer in one move. Every figure on the deck is "
        "on this page with its source.",
    )
    return slide



def why_act_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "Why anybody acts")

    frame = text_box(slide, MARGIN, Inches(1.0), Inches(11.6), Inches(1.0))
    write(frame, "Nobody changes their day for a weather forecast.", 32, INK, DISPLAY, False, 8, first=True)
    write(
        frame,
        "Ghana already has weather warnings. People read them and carry on, because rain "
        "is not news and a forecast asks nothing of you.",
        16,
        MUTED,
        BODY,
        False,
        0,
        line=1.4,
    )

    left_frame = text_box(slide, MARGIN, Inches(2.55), Inches(5.4), Inches(3.2))
    write(left_frame, "WHAT A WEATHER SERVICE SAYS", 11, MUTED, BODY, True, 12, spacing=1.6, first=True)
    write(left_frame, "\u201cHeavy rain expected Thursday.\u201d", 22, MUTED, DISPLAY, False, 14, line=1.2)
    write(left_frame, "Severity: it rains every year.", 14, MUTED, BODY, False, 4, line=1.35)
    write(left_frame, "Is it about me: not obviously.", 14, MUTED, BODY, False, 4, line=1.35)
    write(left_frame, "What do I do: nothing is asked.", 14, MUTED, BODY, False, 12, line=1.35)
    write(left_frame, "Result: nothing changes.", 15, MUTED, BODY, True, 0)

    right_frame = text_box(slide, Inches(6.9), Inches(2.55), Inches(5.6), Inches(3.2))
    write(right_frame, "WHAT CLIMAHEALTH SAYS", 11, ACCENT, BODY, True, 12, spacing=1.6, first=True)
    write(
        right_frame,
        "\u201cMalaria risk is rising here. Cases in 2 to 6 weeks. "
        "Children under five and pregnant women are most at risk. "
        "Empty standing water tonight.\u201d",
        18,
        INK,
        DISPLAY,
        False,
        14,
        line=1.25,
    )
    write(right_frame, "Severity: a named disease.", 14, INK, BODY, False, 4, line=1.35)
    write(right_frame, "Is it about me: my district, my children.", 14, INK, BODY, False, 4, line=1.35)
    write(right_frame, "What do I do: one thing, tonight, free.", 14, INK, BODY, False, 12, line=1.35)
    write(right_frame, "Result: something to actually do.", 15, ACCENT, BODY, True, 0)

    hairline(slide, Inches(6.0))
    close = text_box(slide, MARGIN, Inches(6.2), CONTENT_WIDTH, Inches(1.0))
    write(
        close,
        "We do not warn people about the weather. We warn them about what it is "
        "about to do to their children, and give them one thing to do about it.",
        17,
        INK,
        BODY,
        True,
        6,
        first=True,
    )
    write(
        close,
        "Protection Motivation Theory: action requires severity, personal vulnerability, "
        "and a response the person believes they can carry out. Fear on its own produces "
        "avoidance, not protection, which is why every warning here ends in an action.",
        12,
        FAINT,
        BODY,
        False,
        0,
        line=1.35,
    )
    notes(
        slide,
        "This is your strongest slide. Deliver the left column flatly and the right "
        "column with weight. Then the line: we do not warn people about the weather, "
        "we warn them about what it is about to do to their children. "
        "If a judge pushes on fear tactics, the answer is on the slide: fear without "
        "an action backfires, so every warning we send ends in one thing to do tonight.",
    )
    return slide


def retention_slide(presentation):
    slide = blank(presentation)
    eyebrow(slide, "Why they come back")

    frame = text_box(slide, MARGIN, Inches(1.0), Inches(11.6), Inches(1.0))
    write(frame, "The reward is the thing they were going without.", 32, INK, DISPLAY, False, 8, first=True)
    write(
        frame,
        "About 44% of Ghanaians hold no active NHIS cover. The people most exposed to "
        "climate-driven illness are the same people who cannot afford the premium.",
        16,
        MUTED,
        BODY,
        False,
        0,
        line=1.4,
    )

    loop = [
        ("Open it", "A warning that names your district and your risk"),
        ("Learn one thing", "Five questions, and the reason behind each answer"),
        ("Earn", "Points for every answer, right or wrong"),
        ("Get covered", "3,500 points is a year of NHIS cover"),
    ]
    left = MARGIN
    for index, (name, detail) in enumerate(loop):
        column = text_box(slide, left, Inches(2.7), Inches(2.85), Inches(1.6))
        write(column, f"0{index + 1}", 13, ACCENT, DISPLAY, True, 6, first=True)
        write(column, name, 18, INK, BODY, True, 4)
        write(column, detail, 13, MUTED, BODY, False, 0, line=1.35)
        if index < len(loop) - 1:
            arrow = text_box(slide, left + Inches(2.85), Inches(2.75), Inches(0.4), Inches(0.4))
            write(arrow, "\u2192", 16, FAINT, BODY, False, first=True)
        left += Inches(3.05)

    hairline(slide, Inches(4.65))
    reasons = [
        (
            "It pays in health, not cash",
            "A person who skips the premium is exactly who this reaches. "
            "The reward removes the cost that kept them out.",
        ),
        (
            "The streak forgives",
            "One missed day a week is forgiven. People miss days for illness, "
            "travel, a dead battery, or the flood we just warned them about.",
        ),
        (
            "Wrong answers still earn",
            "Getting it wrong is the best moment to read why, so that is exactly "
            "when the explanation appears. Nobody is locked out of health information.",
        ),
    ]
    left = MARGIN
    for name, detail in reasons:
        column = text_box(slide, left, Inches(4.95), Inches(3.6), Inches(1.9))
        write(column, name, 15, ACCENT, BODY, True, 6, line=1.3, first=True)
        write(column, detail, 13, MUTED, BODY, False, 0, line=1.45)
        left += Inches(3.9)

    notes(
        slide,
        "Adoption is the question every judge asks and most teams wave at. "
        "Say the number: 44% have no active cover. Then say the loop pays in exactly "
        "the thing they are going without. That is not a gimmick, it is the wedge.",
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
        "the adult premium runs GHS 7.20 to 48 by income band, about GHS 30 to 50 a "
        "year for informal workers. We price a point at one pesewa and take the "
        "middle of that band.",
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

    hairline(slide, Inches(5.7))
    figures = [
        ("38.3m", "mobile connections, 110% of the population"),
        ("69.9%", "use the internet, so three in ten do not"),
        ("0 kb", "of data needed to dial the USSD shortcode"),
    ]
    left = MARGIN
    for value, label in figures:
        column = text_box(slide, left, Inches(5.95), Inches(3.9), Inches(0.9))
        write(column, value, 26, ACCENT, DISPLAY, False, 2, first=True)
        write(column, label, 12, MUTED, BODY, False, 0, line=1.3)
        left += Inches(3.9)

    footnote = text_box(slide, MARGIN, Inches(6.95), CONTENT_WIDTH, Inches(0.35))
    write(footnote, "GSMA Intelligence / DataReportal, Digital 2025 Ghana", 10, FAINT, BODY, False, first=True)
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
            "Cash removed. Points buy NHIS cover priced against the real GHS 7.20-48 "
            "premium band, issued by Ghana Health Service, not by us.",
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

    frame = text_box(slide, MARGIN, Inches(1.15), Inches(11.6), Inches(2.4))
    write(frame, "CLIMAHEALTH PREDICT", 12, ACCENT, BODY, True, 18, spacing=2.2, first=True)
    write(frame, "The climate signal is already there.", 34, INK, DISPLAY, False, 2, line=1.1)
    write(frame, "We turn it into a warning", 34, INK, DISPLAY, False, 2, line=1.1)
    write(frame, "somebody can act on.", 34, ACCENT, DISPLAY, False, 0, line=1.1)

    hairline(slide, Inches(3.75))
    facts = [
        ("260", "districts evaluated daily"),
        ("5", "disease pathways, explainable"),
        ("3", "ways in: app, USSD, SMS"),
        ("963", "tests passing"),
    ]
    left = MARGIN
    for value, label in facts:
        column = text_box(slide, left, Inches(3.95), Inches(2.85), Inches(0.95))
        write(column, value, 28, ACCENT, DISPLAY, False, 2, first=True)
        write(column, label, 12, MUTED, BODY, False, 0, line=1.3)
        left += Inches(3.05)

    hairline(slide, Inches(5.15))
    ask = text_box(slide, MARGIN, Inches(5.4), Inches(11.6), Inches(1.8))
    write(ask, "WHAT WE ARE ASKING FOR", 11, MUTED, BODY, True, 10, spacing=1.6, first=True)
    write(
        ask,
        "One district and one season. Give us Madina and a Ghana Health Service link, "
        "and we will run the engine against DHIMS2 case records for a full season to "
        "show how early the warning actually was.",
        17,
        INK,
        BODY,
        False,
        8,
        line=1.4,
    )
    write(
        ask,
        "That is the one thing standing between a defensible model and a validated one, "
        "and it is the only thing we cannot build ourselves.",
        14,
        MUTED,
        BODY,
        False,
        0,
        line=1.4,
    )

    notes(
        slide,
        "Close on the three lines, pause, then the ask. Do not add anything after the "
        "ask. Naming the one thing you cannot do alone reads as confidence, and it "
        "gives the judges something concrete to say yes to.",
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
    burden_slide(presentation)
    problem_slide(presentation)
    solution_slide(presentation)
    why_act_slide(presentation)
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
    accessibility_slide(presentation)
    screenshot_slide(
        presentation,
        "The renewal queue",
        "Ghana Health Service sees who has earned cover, and who is close.",
        "Ranked by points, with the phone number to reach them on. Under-18s are flagged "
        "as already exempt rather than shown a target.",
        "w2-renewals.png",
        "Point at Kofi Mensah: 20 points to go. Say: that is one more day of use. "
        "This is the screen that makes the reward real to an officer.",
        "NHIS renewals \u00b7 Ghana Health Service only \u00b7 seeded demonstration Guardians",
    )
    reward_slide(presentation)
    retention_slide(presentation)
    reach_slide(presentation)
    answers_slide(presentation)
    close_slide(presentation)
    sources_slide(presentation)
    backup_slide(presentation)

    presentation.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    path = build()
    print(f"{path}  ({path.stat().st_size / 1024:.0f} KB)")
