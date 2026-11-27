"""Check the public MFCSC example and write a local report for Firefox."""
from pathlib import Path
import html
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 16})

root = Path.home() / "neurodesktop-storage/mfcsc-demo"
pairs = [line.split() for line in (root / "input/FC_SC_list.txt").read_text().splitlines() if line.strip()]
mask_file = root / "output/mask.csv"
mask = np.loadtxt(mask_file, delimiter=",").astype(bool)
files = sorted((root / "output").glob("mFCSC-*-masked.csv"))
assert len(files) == len(pairs), "A mismatch matrix is required for every input pair"
assert mask.shape == (84, 84), "The public example uses 84 regions"
invalid = nonfinite = affected = zero_sc = 0
common_valid = mask.copy()
sc_files = {f"mFCSC-{Path(fc).stem}-{Path(sc).stem}-masked.csv": sc for fc, sc in pairs}
assert {file.name for file in files} == set(sc_files), "Output filenames must match the supplied input pairs"
for file in files:
    matrix = np.loadtxt(file, delimiter=",")
    assert matrix.shape == mask.shape, file.name
    bad = mask & ~np.isfinite(matrix)
    nonfinite += int(bad.sum())
    affected += int(bad.any())
    if bad.any():
        # The supplied SC files have .csv names but use whitespace delimiters.
        sc = np.loadtxt(root / "input/SC" / sc_files[file.name])
        zero_sc += int((bad & (sc == 0)).sum())
    invalid += np.count_nonzero(mask & (matrix == -999))
    common_valid &= np.isfinite(matrix) & (matrix != -99) & (matrix != -999)
assert common_valid.any(), "No common valid connections remain"
np.savetxt(root / "common-valid-mask.csv", common_valid.astype(int), fmt="%d", delimiter=",")

matrix = np.loadtxt(files[0], delimiter=",")
valid = common_valid
shown = np.ma.masked_where(~valid, matrix)
limit = max(float(np.max(np.abs(matrix[valid]))), 1e-9)
fig, ax = plt.subplots(figsize=(9, 6), layout="constrained")
palette = plt.get_cmap("PRGn").copy()
palette.set_bad("#e8e8e8")
image = ax.imshow(shown, cmap=palette, vmin=-limit, vmax=limit, interpolation="nearest")
ax.set(title="Example participant: masked mFCSC", xlabel="Region index", ylabel="Region index")
ax.axvline(41.5, color="#456b1b", linewidth=0.7)
ax.axhline(41.5, color="#456b1b", linewidth=0.7)
fig.colorbar(image, ax=ax, label="mFCSC")
picture = root / "mfcsc-example.png"
fig.savefig(picture, dpi=160)
plt.close(fig)

summary = (f"Participant matrices: {len(files)}\nMatrix shape: {mask.shape[0]} x {mask.shape[1]}\n"
           f"Connections selected by final mask: {int(mask.sum())}\n"
           f"Non-finite selected values: {nonfinite} across {affected} participants\n"
           f"Non-finite values coinciding with zero input SC: {zero_sc}\n"
           f"Invalid -999 values inside the mask: {invalid}\n"
           f"Connections valid across all participants: {int(common_valid.sum())}\n")
reference = root / "reference"
if reference.is_dir():
    close = matching_nan = 0
    max_difference = 0.0
    for file in files:
        actual = np.loadtxt(file, delimiter=",")
        expected = np.loadtxt(reference / file.name, delimiter=",")
        matching_nan += int(np.array_equal(np.isnan(actual), np.isnan(expected)))
        close += int(np.allclose(actual, expected, rtol=0, atol=1.1e-5, equal_nan=True))
        finite = np.isfinite(actual) & np.isfinite(expected)
        max_difference = max(max_difference, float(np.max(np.abs(actual[finite] - expected[finite]))))
    same_mask = np.array_equal(mask, np.loadtxt(reference / "mask.csv", delimiter=",").astype(bool))
    comparison = (f"Reference matches within 1.1e-5: {close}/{len(files)}\n"
                  f"Matching reference NaN patterns: {matching_nan}/{len(files)}\n"
                  f"Largest finite difference: {max_difference:.6g}\n"
                  f"Identical original masks: {same_mask}\n")
    (root / "reference-check.txt").write_text(comparison)
    summary += "\n" + comparison
(root / "result-check.txt").write_text(summary)
report = root / "mfcsc-report.html"
report.write_text("""<!doctype html><html lang="en"><meta charset="utf-8">
<title>MFCSC example results</title><style>
body{font:16px sans-serif;max-width:1150px;margin:12px auto;padding:0 20px;color:#182313}
h1{color:#456b1b;font-size:28px;margin:12px 0}
main{display:grid;grid-template-columns:0.9fr 1.4fr;gap:16px;align-items:start}
pre{font-size:16px;line-height:1.4;white-space:pre-wrap;background:#f0f5ea;padding:12px}
img{display:block;max-width:100%;max-height:430px;margin:auto}p{line-height:1.3}
@media(max-width:800px){main{display:block}}
</style><h1>MFCSC: public example results</h1><main><pre>""" + html.escape(summary)
    + "</pre><img src='mfcsc-example.png' alt='Masked mismatch matrix'></main>"
    + "<p>Grey cells are excluded by the final mask, have an invalid sentinel value, "
      "or are non-finite in at least one participant. "
      "The lower triangle and between-hemisphere blocks are excluded by this run's defaults.</p>"
    + "<p>The original results are unchanged. The separate common-valid-mask.csv is a conservative "
      "QC mask for comparing the same valid connections across participants.</p>"
    + "<p>Example file: " + html.escape(files[0].name) + "</p></html>")
print(summary, end="")
print(f"Report: {report}")
