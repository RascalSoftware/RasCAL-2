import zipfile
from io import StringIO

import numpy as np
from ratapi.outputs import BayesResults, bayes_results_fields, results_fields


def write_result_to_zipped_csvs(filename, results):
    """Write data from the calculation results to a CSV files in zip file.

    Parameters
    ----------
    filename: str or Path
        The path to the zip file.
    results: str or Path
        The calculation result.

    """
    fmt = "%.8f"
    delimiter = ", "
    with zipfile.ZipFile(filename, "w") as f:
        for list_field in results_fields["list_fields"]:
            for i, array in enumerate(getattr(results, list_field)):
                text_buffer = StringIO()
                np.savetxt(text_buffer, array, fmt=fmt, delimiter=delimiter)
                f.writestr(f"{list_field}_contrast{i}.csv", text_buffer.getvalue())

        for list_field in results_fields["double_list_fields"]:
            actual_list = getattr(results, list_field)
            for i in range(len(actual_list)):
                for j, array in enumerate(actual_list[i]):
                    domain = "" if len(actual_list[i]) == 1 else f"_domain{j}"
                    text_buffer = StringIO()
                    np.savetxt(text_buffer, array, fmt=fmt, delimiter=delimiter)
                    f.writestr(f"{list_field}_contrast{i}{domain}.csv", text_buffer.getvalue())

        contrast_param_fields = [
            "scalefactors",
            "bulkIn",
            "bulkOut",
            "subRoughs",
            "resample",
        ]
        for field in contrast_param_fields:
            text_buffer = StringIO()
            np.savetxt(text_buffer, getattr(results.contrastParams, field), fmt=fmt, delimiter=delimiter)
            f.writestr(f"contrastParams/{field}.csv", text_buffer.getvalue())

        if not isinstance(results, BayesResults):
            return

        procedure_field = "nestedSamplerOutput" if results.from_procedure() == "ns" else "dreamOutput"
        for inner_class in ["predictionIntervals", "confidenceIntervals", procedure_field]:
            subclass = getattr(results, inner_class)

            for field in bayes_results_fields["list_fields"][inner_class]:
                for i, array in enumerate(getattr(subclass, field)):
                    text_buffer = StringIO()
                    np.savetxt(text_buffer, array, fmt=fmt, delimiter=delimiter)
                    f.writestr(f"Bayes/{inner_class}_{field}_contrast{i}.csv", text_buffer.getvalue())

            for field in bayes_results_fields["double_list_fields"][inner_class]:
                actual_list = getattr(subclass, field)
                for i in range(len(actual_list)):
                    for j, array in enumerate(actual_list[i]):
                        domain = "" if len(actual_list[i]) == 1 else f"_domain{j}"
                        text_buffer = StringIO()
                        np.savetxt(text_buffer, array, fmt=fmt, delimiter=delimiter)
                        f.writestr(f"Bayes/{inner_class}_{field}_contrast{i}{domain}.csv", text_buffer.getvalue())

            for field in bayes_results_fields["array_fields"][inner_class]:
                array = getattr(subclass, field)
                if field == "allChains":
                    # allChains is 3D so convert to 2D
                    array = array.reshape(-1, array.shape[-1])
                text_buffer = StringIO()
                np.savetxt(text_buffer, array, fmt=fmt, delimiter=delimiter)
                f.writestr(f"Bayes/{inner_class}_{field}.csv", text_buffer.getvalue())
