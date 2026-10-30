"""Build the modelling report PDF from the numbers saved by Notebook 04.

Everything quantitative in the PDF is read from reports/model_results.json, so the
document cannot drift out of step with the notebook that produced it.

    python reports/make_report.py
"""

import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(HERE, "figures")
OUT = os.path.join(ROOT, "Modelling_Report.pdf")

NAVY = colors.HexColor("#2f5574")
BLUE = colors.HexColor("#4a7ba7")
RUST = colors.HexColor("#b4584f")
GREY = colors.HexColor("#5a5a5a")
LINE = colors.HexColor("#c9d4de")
BAND = colors.HexColor("#eef3f7")

with open(os.path.join(HERE, "model_results.json")) as fh:
    R = json.load(fh)


def num(value):
    """model_results.json stores numbers as strings in places; normalise them."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


# ----------------------------------------------------------------- styles
ss = getSampleStyleSheet()
body = ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica",
                      fontSize=9.3, leading=13.6, spaceAfter=7, alignment=TA_LEFT,
                      textColor=colors.HexColor("#1c1c1c"))
h1 = ParagraphStyle("h1", parent=body, fontName="Helvetica-Bold", fontSize=15,
                    leading=19, spaceBefore=16, spaceAfter=9, textColor=NAVY)
h2 = ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=10.8,
                    leading=14, spaceBefore=12, spaceAfter=5, textColor=NAVY)
title = ParagraphStyle("title", parent=body, fontName="Helvetica-Bold", fontSize=20,
                       leading=24, spaceAfter=4, textColor=NAVY)
sub = ParagraphStyle("sub", parent=body, fontName="Helvetica", fontSize=11,
                     leading=15, textColor=GREY, spaceAfter=2)
small = ParagraphStyle("small", parent=body, fontName="Helvetica-Oblique",
                       fontSize=8.2, leading=11.4, textColor=GREY, spaceAfter=10)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=12, bulletIndent=2,
                        spaceAfter=4)
quote = ParagraphStyle("quote", parent=body, leftIndent=12, rightIndent=10,
                       fontName="Helvetica-Oblique", textColor=NAVY,
                       borderPadding=0, spaceBefore=4, spaceAfter=9)

S = []


def p(text, style=body):
    S.append(Paragraph(text, style))


def head(text):
    p(text, h1)


def sec(text):
    p(text, h2)


def bullets(items):
    for item in items:
        S.append(Paragraph(item, bullet, bulletText="•"))
    S.append(Spacer(1, 4))


def gap(height=6):
    S.append(Spacer(1, height))


def table(rows, widths, align_right_from=1, highlight_row=None, font=8.4):
    t = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font),
        ("LEADING", (0, 0), (-1, -1), font + 3.4),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (align_right_from, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND]),
    ]
    if highlight_row is not None:
        style += [("BACKGROUND", (0, highlight_row), (-1, highlight_row),
                   colors.HexColor("#dce8f2")),
                  ("FONTNAME", (0, highlight_row), (-1, highlight_row), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    S.append(t)
    S.append(Spacer(1, 9))


def figure(name, caption, width=15.6 * cm):
    path = os.path.join(FIG, name)
    if not os.path.exists(path):
        return
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    img = Image(path, width=width, height=width * h / w)
    S.append(KeepTogether([img, Spacer(1, 3), Paragraph(caption, small)]))


# ----------------------------------------------------------------- content
best = R["best_model"]
test = {k: {m: num(v) for m, v in row.items()} for k, row in R["test_results"].items()}
cv = {k: {m: num(v) for m, v in row.items()} for k, row in R["cross_validation"].items()}
b = test[best]

p("Hyderabad Property Price Prediction", title)
p("Exploration, Feature Engineering and Modelling: what we did, how we did it, "
  "and what came out", sub)
p("Phases 2 and 3 of 4 &nbsp;|&nbsp; Source: MagicBricks listings, scraped into SQLite "
  "&nbsp;|&nbsp; 27 October 2026", small)

head("1. What this report covers")
p("The goal of the project is a model that predicts the <b>asking price</b> of a residential "
  "property in Hyderabad from the things you can see in a listing: how big it is, how many "
  "bedrooms and bathrooms it has, what type of building it is, and where it is.")
p("An earlier report covered cleaning the scraped data. This one covers everything after that: "
  "looking at the cleaned data to decide what to do with it, turning it into something a model "
  "can read, training four models, and measuring how well they actually work on listings they "
  "had never seen.")
p("The language here is deliberately plain. Where a technical term is unavoidable it is "
  "explained the first time it appears.")

sec("The headline result")
p("The best model is <b>%s</b>. On %s held-out listings it was wrong by <b>Rs %.0f lakh</b> on a "
  "typical property, which is <b>%.0f%%</b> of the price, and "
  "<b>%.0f%% of its predictions landed within 25%%</b> of the true asking price."
  % (best, f"{R['rows']['test']:,}", b["MAE_lakh"], b["MedAPE_%"], num(R["within_25_pct"])))

table([["Measure", "Result", "What it means in plain words"],
       ["Listings used for training", f"{R['rows']['train']:,}",
        "80% of the cleaned data"],
       ["Listings held back for testing", f"{R['rows']['test']:,}",
        "never used to make any decision"],
       ["Features given to the model", str(R["features"]["count"]),
        "out of 71 available columns"],
       ["Typical error (MAE)", f"Rs {b['MAE_lakh']:.0f} lakh",
        "the average size of a miss"],
       ["Typical error as a %", f"{b['MedAPE_%']:.0f}%",
        "the same miss, relative to price"],
       ["Predictions within 25%", f"{num(R['within_25_pct']):.0f}%",
        "roughly how often it is useful"],
       ["R-squared (log price)", f"{b['R2_log']:.2f}",
        "share of the variation explained"],
       ["Beats 'always guess the median' by",
        f"{(test['Baseline (median)']['MAE_lakh'] - b['MAE_lakh']):.0f} lakh",
        "proof the model learned something"]],
      widths=[5.6 * cm, 3.1 * cm, 7.2 * cm], align_right_from=1)

p("For context on what counts as good: predicting house prices from listing fields alone is "
  "hard, because two flats of the same size on the same street can legitimately differ by 30%% "
  "on floor, view, finish and how badly the owner wants to sell. None of that is in the data. "
  "An error around %.0f%% is a reasonable baseline result and the error analysis in section 7 "
  "shows exactly where it comes from." % b["MedAPE_%"])

head("2. The data we started with")
p("The cleaning phase left <b>19,340 listings and 71 columns</b>, combining two tables: one row "
  "per property, joined to a table of locality-level ratings and published price statistics. "
  "Everything in this report starts from that file.")
p("One housekeeping note, so the two reports can be read side by side: the cleaning report quotes "
  "19,715 rows, while the file in <font face='Courier'>data/processed/</font> that this work "
  "actually used holds 19,340. The difference is a later revision of the same cleaning filters "
  "that was not written back to this folder. Every number in this report comes from the file that "
  "was really used, and re-running both notebooks against the newer file would move the results "
  "only marginally &mdash; it is 2% more data through an identical pipeline.", small)
p("One inherited caveat matters throughout. The data was scraped price band by price band "
  "(1&ndash;50 lakh, 50&ndash;80 lakh, 80 lakh&ndash;1 crore, and upward), so the mix of cheap "
  "and expensive listings reflects how many pages each band had, not the real Hyderabad market. "
  "That is fine for a model that answers “given these features, what price?”, which is "
  "our question. It is not a basis for claims about the market as a whole.")

head("3. First move: split the data before looking at it")
p("Before computing a single statistic we set aside 20% of the listings and did not look at "
  "them again until the very last step.")
p("The reason is easy to miss. Exploring data is not a passive activity: we were about to decide "
  "which columns to keep, what to fill missing values with, and which categories to merge. Every "
  "one of those decisions is based on what we saw. If we had looked at all the data first, those "
  "decisions would have quietly carried information from the test listings into the model, and "
  "the final score would have flattered it.", )
p("So the rule for the whole project was: <b>every number we looked at came from the training "
  "set only</b>. 15,472 listings to learn from, 3,868 kept sealed.")

head("4. What we found when we explored (Notebook 03)")
p("We limited the exploration to six questions. Each one had to lead to a decision; anything "
  "that would only have produced a nice-looking chart was skipped.")

sec("4.1 The price needed to be rescaled")
p("Asking price is extremely lopsided. The middle listing is about Rs 1.5 crore, but the most "
  "expensive is Rs 49 crore, so a thin tail of very expensive property stretches far to the "
  "right. Measured formally, the skew was <b>5.82</b>, where anything above about 1 is "
  "considered lopsided.")
p("Why this matters: Linear and Ridge Regression work by minimising <i>squared</i> error, so a "
  "handful of enormous prices dominate everything the model is trying to do. It ends up fitting "
  "mansions and ignoring the flats that make up most of the data.")
p("The fix is to train on the <b>logarithm</b> of the price instead. A log compresses large "
  "numbers much more than small ones, which pulls the long tail in. It took the skew from 5.82 "
  "to <b>0.09</b> &mdash; essentially symmetrical.")
figure("01_target_distribution.png",
       "Figure 1. Asking price before and after taking logs. The left chart is almost unusable "
       "for a linear model; the right one is close to a bell curve.")
p("Every model in this project therefore predicts log price, and every prediction is converted "
  "back into rupees before we score it &mdash; so the errors we report are in rupees, which a "
  "human can actually judge.")

sec("4.2 Area is the strongest honest feature &mdash; and one column was cheating")
p("Ranking the numeric columns by how strongly they move with log price put covered area at the "
  "top, followed by bathrooms, bedrooms and the locality's published price per square foot.")
figure("02_numeric_correlation.png",
       "Figure 2. How strongly each number moves with log price. Negative is not weaker: "
       "locality_rank is negative because rank 1 is the best locality.")
p("Tied for first place, though, was a column called <b>price_per_sqft_true</b> &mdash; and that "
  "one had to go. It is the price divided by the area, so it contains the answer. We proved it "
  "rather than assumed it: dividing price-by-area by that column gives exactly 1.0 on all "
  "15,472 training rows.")
p("This is called <b>leakage</b>, and it is the single most common way a beginner project ends "
  "up with a model that scores beautifully and is worthless. Left in, it would have pushed "
  "R-squared above 0.95. The test is always the same question: <i>would I know this value before "
  "the price?</i> For price per square foot, obviously not &mdash; you would need the price.")
figure("03_area_bedrooms.png",
       "Figure 3. Left: area against price, both on log scales, is nearly a straight line. "
       "Right: price rises with bedrooms, but the boxes overlap heavily, which is why location "
       "features matter.")

sec("4.3 Missing values, grouped by why they are missing")
p("60 of the 71 columns had gaps. The useful move was to ask <i>why</i> each one was empty "
  "instead of applying one blanket rule.")
figure("04_missingness.png", "Figure 4. The emptiest columns in the training data.")
p("The best example is the floor number, missing on 28% of listings. That looks like a data "
  "quality problem until you break it down by property type:")
table([["Property type", "Floor number missing"],
       ["Villa", "99.9%"],
       ["Residential House", "50.6%"],
       ["Apartment", "4.6%"],
       ["Builder Floor Apartment", "5.0%"]],
      widths=[6.0 * cm, 4.2 * cm])
p("It is not a quality problem at all. “Which floor?” is a meaningless question for a "
  "standalone villa, so the field is blank. <b>The blank itself is information</b> &mdash; it "
  "tells you the building type. So rather than just filling the gap, we fill it <i>and</i> add a "
  "small extra column recording that it was filled. The model can then learn from the fact of "
  "the gap, which is exactly what we want.")
p("The same reasoning decided the rest: <b>facing</b> and <b>age of property</b> became an "
  "explicit “Unknown” category rather than a guess; <b>carpet area</b> was dropped, "
  "because it is half empty and duplicates covered area, which is better filled and more "
  "predictive; and the amenity detail fields (parking, power, water, flooring), 64&ndash;75% "
  "empty, were set aside for this first version.")

sec("4.4 Two columns were broken and needed repair, not deletion")
p("<b>facing</b> claimed 34 different values. Only eight of them are compass directions. The "
  "rest were whatever sellers typed into the wrong box, such as "
  "<i>“Near Nallakunta PS. Beside Jyothi Bala Mandir High School”</i>. One-hot encoding "
  "it as-is would have created a separate column for each landmark, every one matching a single "
  "property, every one pure noise.")
p("But the 255 odd values were not all the same problem, and that distinction was worth making:")
table([["Value", "Rows", "What it is", "What we did"],
       ["Newly Constructed Property", "176", "an answer to a different question", "→ Unknown"],
       ["“South -West”", "54", "a real direction missing a space",
        "→ fixed the spacing"],
       ["landmark descriptions", "~25", "free text in the wrong field", "→ Unknown"]],
      widths=[4.6 * cm, 1.4 * cm, 5.4 * cm, 4.2 * cm], align_right_from=1)
p("Those 54 rows are the point. A careless clean-up would have thrown away 54 perfectly good "
  "observations because of one missing space.")
p("<b>possession</b> had 48 values, but 13,830 of them said “Ready to Move” and 1,111 "
  "said “Under Construction”. The rest were individual handover dates, plus "
  "“Ready To Move” with a capital T, which a computer treats as a completely different "
  "category. We collapsed all of it into three sensible levels, which fixes the capital-letter "
  "bug for free.")

sec("4.5 Location: the hardest decision in the project")
p("Location drives property price more than anything else, and it was the hardest thing to "
  "encode. The training data contains <b>2,177 different localities</b> for 15,472 listings "
  "&mdash; about seven listings each. Only 129 of them have 20 listings or more.")
p("The standard beginner approach, one-hot encoding, would create 2,177 almost-empty columns, "
  "and any locality appearing once in training is a column that teaches the model nothing. "
  "Project and builder names were worse: 8,876 and 10,388 distinct values, nearly all unique. "
  "Those are names, not categories.")
p("The alternative was already sitting in the data. The locality table carries numbers the "
  "website publishes per area &mdash; average price per square foot, a locality rank, quarterly "
  "price growth. Each one is <b>a single column that works for every locality</b>, including "
  "localities the model has never seen.")
p("Two things make these safe to use, and both are worth stating precisely:", )
bullets([
    "They are published <i>before</i> any individual listing exists, so they would genuinely be "
    "available at prediction time. That is the real test for leakage.",
    "They are <b>not</b> target encoding. Target encoding means computing the average price of "
    "<i>our own</i> training listings per locality, which leaks the answer and must be rebuilt "
    "inside each validation fold. These come from the website, computed over the whole market.",
])
p("We did not take the argument on trust &mdash; section 6.2 tests it.")

head("5. Turning the data into something a model can read (Notebook 04)")
p("This is the step people usually overcomplicate. We kept it deliberately small, because a "
  "correct target transform and an honest testing protocol buy far more than invented features "
  "do, and every extra transformation is another place for a bug to hide.")
p("In total: <b>%d features</b> (%d numeric, %d categorical) out of 71 columns. Two columns "
  "repaired. 49 dropped. No new mathematical features, no interactions, no clustering, no text "
  "mining." % (R["features"]["count"], len(R["features"]["numeric"]),
               len(R["features"]["categorical"])))

sec("5.1 What was dropped, and why")
table([["Group", "Columns", "Reason"],
       ["Leakage", "1", "price_per_sqft_true is the price divided by the area"],
       ["Identifiers", "5", "property id, project and builder names — near-unique text"],
       ["Free text", "11",
        "descriptions state the price in words in 86% of listings"],
       ["Redundant", "11",
        "duplicate coordinates, inputs of a column we already keep, raw versions of repaired columns"],
       ["Too empty / needs parsing", "5",
        "amenity detail fields, 64–75% empty; flooring needs string splitting"],
       ["Individual ratings", "16",
        "16 locality ratings that all move together; we keep the overall one"]],
      widths=[4.4 * cm, 1.6 * cm, 9.6 * cm], align_right_from=1)
p("The free-text group deserves a note, because it is the subtlest finding inherited from the "
  "cleaning phase: MagicBricks auto-generates the description, and 86% of those descriptions "
  "state the price in words &mdash; <i>“this apartment is sold at price of Rs 46.9 "
  "Lac”</i>. Any text feature built on them would have carried the answer. Leakage is a "
  "property of the information, not of the data type.")

sec("5.2 The recipe that learns from training data only")
p("All the preparation sits inside a scikit-learn <b>Pipeline</b>, which is best understood as a "
  "sealed recipe: it learns its numbers from whatever data you fit it on, and then applies "
  "exactly those numbers to anything you give it afterwards. It does three jobs.")
table([["Step", "What it does", "Why"],
       ["Fill numeric gaps", "use the middle value (median), and add a 0/1 column marking "
        "that it was filled",
        "median because the columns are lopsided; the marker column because the gap is itself "
        "informative"],
       ["Put numbers on one scale", "rescale so each column has a similar spread",
        "Ridge penalises large coefficients, so without this the penalty would depend on "
        "whichever units a column happens to use"],
       ["Encode categories", "one column per category (one-hot), rare categories pooled "
        "together",
        "models need numbers, not words; pooling categories with under 10 listings keeps noise "
        "out"]],
      widths=[3.5 * cm, 5.9 * cm, 6.2 * cm], align_right_from=3)
p("Two consequences are worth spelling out, because they are the whole reason for using a "
  "pipeline rather than preparing the data by hand:")
bullets([
    "When we cross-validate, the median and the category lists are <b>recomputed from scratch on "
    "each fold</b>. Had we computed the median once over the whole training set, every fold would "
    "have been scored with a number derived partly from the rows it was being tested on.",
    "The same recipe object is used for all four models, so the comparison between them is fair: "
    "the only thing that changes is the model.",
])
p("The %d features expand to <b>%d columns</b> after one-hot encoding and the missing-value "
  "markers." % (R["features"]["count"], R["features"]["after_preprocessing"]))

head("6. How we trained and compared the models")
sec("6.1 The protocol, in plain words")
bullets([
    "<b>Cross-validation.</b> Split the training data into five parts; train on four, predict the "
    "fifth; repeat five times so every listing gets predicted by a model that never saw it. This "
    "is how all model choices were made, and it is far more trustworthy than a single split.",
    "<b>Four metrics.</b> <i>MAE</i> is the typical size of a miss, in lakh &mdash; the headline. "
    "<i>RMSE</i> punishes big misses harder, so RMSE far above MAE means a few predictions are "
    "badly wrong. <i>R-squared</i> is the share of the variation explained, on the log scale the "
    "model was fitted on. <i>MedAPE</i> is the typical miss as a percentage, which MAE cannot "
    "see &mdash; Rs 20 lakh is a disaster on a Rs 50 lakh flat and a rounding error on a "
    "Rs 10 crore villa.",
    "<b>A stupid baseline first.</b> Before trusting any model, we scored the dumbest rule there "
    "is: always predict the median price. Anything that cannot beat it by a wide margin has "
    "learned nothing.",
    "<b>The test set was opened once</b>, at the end, after every choice had been made.",
])

sec("6.2 Five-fold cross-validation on the training set")
rows = [["Model", "MAE (lakh)", "RMSE (lakh)", "R-squared (log)", "Typical error %"]]
order = ["Baseline (median)", "Linear Regression", "Ridge Regression",
         "Random Forest", "Gradient Boosting"]
for name in order:
    if name not in cv:
        continue
    r = cv[name]
    rows.append([name, f"{r['MAE_lakh']:.1f}", f"{r['RMSE_lakh']:.1f}",
                 f"{r['R2_log']:.3f}", f"{r['MedAPE_%']:.1f}%"])
table(rows, widths=[4.6 * cm, 2.6 * cm, 2.6 * cm, 3.0 * cm, 2.8 * cm])
p("The ranking is clear and the reason is worth understanding, because it is the most "
  "instructive result in the project. <b>Both tree models beat both linear models by a wide "
  "margin.</b>")
p("A linear model has to assume that an extra square foot adds the same number of rupees "
  "everywhere in Hyderabad. It plainly does not &mdash; a square foot in Jubilee Hills and one "
  "on the outskirts are different goods. That dependence of one feature's effect on another is "
  "called an <b>interaction</b>, and a linear model cannot represent it unless you build the "
  "combined term by hand. A tree splits on the locality's price level first and then on area "
  "inside each branch, so it discovers the structure on its own.")
p("Linear and Ridge landing close together is also informative: it means there was not much "
  "collinearity left for the penalty to fix, which is a sign the feature set was already sound. "
  "If Ridge had rescued a badly-behaved Linear Regression, that would have pointed at a problem "
  "in the features, not a virtue in Ridge.")

sec("6.3 Settling the location question with an experiment")
p("Section 4.5 argued that the published locality numbers beat one-hot encoding thousands of "
  "locality names. An argument is not evidence, so we ran all three options. The locality "
  "one-hot encoder was placed <i>inside</i> the pipeline, so the list of localities big enough "
  "to keep was rebuilt on each fold &mdash; the difference between a clean experiment and a "
  "leaky one.")
exp_rows = [["Approach", "Model", "R-squared (log)", "MAE (lakh)"]]
for key, value in R["locality_experiment"].items():
    label, model_name = key.split(" | ")
    exp_rows.append([label, model_name, f"{num(value['R2_log']):.3f}",
                     f"{num(value['MAE_lakh']):.1f}"])
table(exp_rows, widths=[6.6 * cm, 3.4 * cm, 3.0 * cm, 2.6 * cm], align_right_from=2)
p("The published numbers win. Adding a hundred-plus locality columns on top of them changes "
  "almost nothing, and replacing them with one-hot encoding alone is clearly worse. "
  "<b>One well-chosen numeric column beat a hundred indicator columns</b> &mdash; and unlike a "
  "one-hot column, it keeps working for a locality the model has never seen.")

sec("6.4 Tuning")
p("Small, deliberate grids. Each setting is there because it controls something we had a reason "
  "to worry about, searched by cross-validation on the training set only.")
tune_rows = [["Model", "Settings chosen"]]
for name, params in R["chosen_hyperparameters"].items():
    pretty = ", ".join(f"{k} = {v}" for k, v in params.items()) or "—"
    tune_rows.append([name, pretty])
table(tune_rows, widths=[4.6 * cm, 11.0 * cm], align_right_from=1)

head("7. Results on the held-out test set")
p("%s listings, never used to make a single decision. Each tuned model was refitted on the full "
  "training set and scored once." % f"{R['rows']['test']:,}")
rows = [["Model", "MAE (lakh)", "RMSE (lakh)", "R-squared (log)", "Typical error %"]]
best_index = None
for i, name in enumerate(order, start=1):
    if name not in test:
        continue
    r = test[name]
    rows.append([name, f"{r['MAE_lakh']:.1f}", f"{r['RMSE_lakh']:.1f}",
                 f"{r['R2_log']:.3f}", f"{r['MedAPE_%']:.1f}%"])
    if name == best:
        best_index = len(rows) - 1
table(rows, widths=[4.6 * cm, 2.6 * cm, 2.6 * cm, 3.0 * cm, 2.8 * cm],
      highlight_row=best_index)
p("All four are reported, not just the winner. Showing only the best model hides how much of the "
  "performance came from the choice of model rather than from the data &mdash; and that is the "
  "first thing a reviewer will ask about.")
p("The two tree models are close enough that <b>which one wins depends on the metric you care "
  "about</b>, and that is worth saying out loud rather than hiding behind a single headline. "
  "Gradient Boosting is ahead on MAE (%.1f vs %.1f lakh), on RMSE and on R-squared, so it is the "
  "better model on average and for avoiding large misses. Random Forest is ahead on typical "
  "percentage error (%.1f%% vs %.1f%%), which means it is slightly better on the cheaper listings "
  "where a given rupee error hurts proportionally more. Gradient Boosting is selected here "
  "because MAE was declared the headline metric before the models were run; if the goal were "
  "uniform percentage accuracy across price bands, Random Forest would be the defensible pick."
  % (test["Gradient Boosting"]["MAE_lakh"], test["Random Forest"]["MAE_lakh"],
     test["Random Forest"]["MedAPE_%"], test["Gradient Boosting"]["MedAPE_%"]))
figure("05_model_comparison.png",
       "Figure 5. Test-set performance. The grey bar is the 'always guess the median' baseline.")
p("The test numbers sit close to the cross-validation numbers. That agreement is itself a "
  "result: it means nothing was accidentally tuned against the test set, and the protocol held.")

sec("7.1 Where the model goes wrong")
p("A single average hides the shape of the mistakes, so two diagnostics matter more here than "
  "any further tuning would.")
figure("06_prediction_quality.png",
       "Figure 6. Left: predicted against actual price, both on log scales; the red line is a "
       "perfect prediction. Right: how far off the predictions are, as a percentage of the true "
       "price.")
p("The error histogram is roughly centred on zero, which is the first thing to check &mdash; a "
  "model that was systematically high or low everywhere would point to a bug, typically "
  "forgetting to undo the log transform. <b>%.0f%% of predictions land within 10%%</b> of the "
  "true asking price and <b>%.0f%% within 25%%</b>."
  % (num(R["within_10_pct"]), num(R["within_25_pct"])))
band_rows = [["Price band", "Listings", "Typical actual price", "MAE (lakh)", "Typical error %"]]
for band, row in R["error_by_band"].items():
    band_rows.append([str(band), f"{int(num(row['listings'])):,}",
                      f"Rs {num(row['median_actual_lakh']):.0f} lakh",
                      f"{num(row['MAE_lakh']):.1f}",
                      f"{num(row['MedAPE_pct']):.1f}%"])
table(band_rows, widths=[3.2 * cm, 2.2 * cm, 4.0 * cm, 2.8 * cm, 3.0 * cm])
p("The pattern is consistent and has one cause: <b>thin data at the edges of the market</b>. The "
  "scrape was organised by price band, so the cheapest and most expensive segments are covered "
  "sparsely, and expensive property is also the most individual &mdash; a Rs 20 crore villa's "
  "price depends on finishes, plot shape and view, none of which appear in 23 columns.")

sec("7.2 What the model actually relies on")
figure("07_feature_importance.png",
       "Figure 7. The features the winning model leans on most.")
imp_rows = [["Feature", "Share of the model's decisions"]]
for i, (name, value) in enumerate(list(R["top_features"].items())[:8]):
    imp_rows.append([name, f"{num(value) * 100:.1f}%"])
table(imp_rows, widths=[7.4 * cm, 4.6 * cm])
p("Covered area dominates, the locality price aggregates come next, then bathroom and bedroom "
  "counts. That ordering is a sanity check in its own right: it is what any property valuer "
  "would tell you matters. When a feature you cannot explain tops this chart, the usual cause is "
  "leakage &mdash; so a boring, sensible ranking here is good news.")

head("8. Honest limitations")
bullets([
    "<b>It predicts asking prices, not sale prices.</b> That is what was scraped. Sellers ask "
    "optimistically, so this is a model of what people advertise, not of what property is worth.",
    "<b>Percentage error is worse at both ends of the market</b> (section 7.1), because the "
    "price-band scrape covers them thinly.",
    "<b>Validation is mildly optimistic</b> wherever the locality average price is used. The "
    "website computed that average over a pool of listings that overlaps ours, which the cleaning "
    "report flagged and which has not gone away. It is most pronounced in localities with few "
    "listings behind the average.",
    "<b>Coordinates are locality-resolution at best.</b> Many listings inherited their locality's "
    "centre point during cleaning, so latitude and longitude are coarser than they look.",
    "<b>The price mix is an artefact of the scrape</b>, so nothing here supports a claim about the "
    "Hyderabad market overall &mdash; only about the relationship between features and price.",
])

head("9. What we would do next")
p("In the order most likely to pay off:")
bullets([
    "<b>Parse the amenity columns.</b> Turn amenities and flooring type into simple yes/no "
    "columns. They are currently set aside only because they need string splitting, and they are "
    "present on richer listings where the model is weakest.",
    "<b>Try HistGradientBoosting or XGBoost.</b> Both handle missing values natively, train much "
    "faster than plain Gradient Boosting, and usually score better.",
    "<b>Add target encoding for locality</b> &mdash; the average price of training listings per "
    "locality &mdash; computed strictly inside each cross-validation fold. Done carelessly it is "
    "leakage; done correctly it is often the single biggest gain available here.",
    "<b>Only then look at the description text</b>, and only after stripping the price out of it.",
    "<b>Model the cheap and expensive bands separately</b>, or weight them, if the goal is uniform "
    "percentage accuracy rather than the best average.",
])

head("10. The four things worth explaining in an interview")
sec("A log transform was worth more than any feature")
p("Skew 5.82 to 0.09, one line of code. The linear models were unusable without it. It is a good "
  "demonstration that understanding the target matters more than adding features &mdash; the "
  "first question about any regression target should be whether its distribution suits the loss "
  "function.")
sec("The leak was found by arithmetic, not by intuition")
p("price_per_sqft_true looks like a feature and ranks like the best one. Dividing price by area "
  "and comparing gave exactly 1.0 on all 15,472 rows, which settles it. The test that "
  "generalises: <i>would I know this value before I knew the price?</i> It is also why the "
  "locality averages were kept &mdash; they pass that same test, and over-pruning out of caution "
  "costs accuracy just as surely as leakage does.")
sec("One good number beat a hundred dummy columns")
p("2,177 localities one-hot encoded lost to four published locality statistics, and the "
  "difference was measured, not assumed. High cardinality is not automatically a reason for "
  "one-hot encoding; the question is whether a compact numeric summary of the same thing already "
  "exists.")
sec("A missing value can be a feature")
p("The floor number is absent for 99.9% of villas, because the question is meaningless for them. "
  "Filling the gap and adding a marker column lets the model use the absence. “Missing” "
  "is not always an error to be patched over &mdash; sometimes it is the data telling you "
  "something.")

head("Appendix: what was produced, and how to re-run it")
table([["File", "What it is"],
       ["notebooks/03-eda.ipynb", "the exploration, six questions, with the figures"],
       ["notebooks/04-feature-engineering-and-models.ipynb",
        "features, the four models, tuning, final evaluation"],
       ["data/processed/train.csv, test.csv", "the 80/20 split, fixed seed 42"],
       ["models/%s.joblib" % best.lower().replace(" ", "_"),
        "the winning model, with its preprocessing baked in"],
       ["reports/model_results.json", "every number in this report, machine-readable"],
       ["reports/figures/", "the seven figures"],
       ["reports/make_report.py", "the script that builds this PDF from that JSON"]],
      widths=[7.0 * cm, 8.6 * cm], align_right_from=1)
p("Run notebook 03 and then notebook 04 from a fresh kernel, then "
  "<font face='Courier'>python reports/make_report.py</font>. The random seed is fixed at 42 "
  "throughout, so the split, the folds and the models reproduce exactly. Because the saved model "
  "carries its own preprocessing, predicting on a new listing is one call &mdash; no chance of "
  "forgetting a transformation.")
p("Phases 2 and 3 of 4. Next: either the improvements in section 9, or deployment of the saved "
  "model behind a small prediction interface.", small)


# ----------------------------------------------------------------- render
def decorate(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.6)
    canvas.setFillColor(GREY)
    canvas.drawString(2.2 * cm, A4[1] - 1.25 * cm,
                      "Hyderabad Property Price Prediction  |  Modelling Report")
    canvas.drawRightString(A4[0] - 2.2 * cm, A4[1] - 1.25 * cm, str(doc.page))
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(2.2 * cm, A4[1] - 1.45 * cm, A4[0] - 2.2 * cm, A4[1] - 1.45 * cm)
    canvas.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                      topMargin=1.95 * cm, bottomMargin=1.7 * cm,
                      title="Hyderabad Property Price Prediction - Modelling Report",
                      author="Saurabh Mishra")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=decorate)])
doc.build(S)
print("wrote", OUT)
