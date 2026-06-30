import weka.core.jvm as jvm
from weka.attribute_selection import ASEvaluation, AttributeSelection, ASSearch
from weka.core.converters import Loader

jvm.start(packages=True)

for name, arff_file in [("7 วัน", "dam_risk_forecast_7days.arff"), ("30 วัน", "dam_risk_forecast_30days.arff")]:
    print(f"{'='*60}")
    print(f"  InfoGain — {name}")
    print(f"{'='*60}")

    loader = Loader("weka.core.converters.ArffLoader")
    data = loader.load_file(arff_file)
    data.class_is_last()

    eval_ig = ASEvaluation(classname="weka.attributeSelection.InfoGainAttributeEval")
    search = ASSearch(classname="weka.attributeSelection.Ranker", options=["-T", "-1.7976931348623157E308", "-N", "-1"])
    attsel = AttributeSelection()
    attsel.set_evaluator(eval_ig)
    attsel.set_search(search)
    attsel.select_attributes(data)

    results = attsel.results
    print(results)
    print()

jvm.stop()
