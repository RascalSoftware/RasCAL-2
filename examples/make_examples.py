from pathlib import Path

import ratapi as rat

examples = [
    "DSPC_custom_XY",
    "DSPC_custom_layers",
    "DSPC_standard_layers",
    "absorption",
    "domains_custom_XY",
    "domains_custom_layers",
    "domains_standard_layers",
]

for example in examples:
    p, _ = getattr(rat.examples, example)()
    example_folder = Path(f"./{example}/")
    example_folder.mkdir(parents=True, exist_ok=True)
    p.save(example_folder, "project")
    rat.Controls().save(example_folder, "controls") 
