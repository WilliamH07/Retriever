"""Reproducible preliminary calculations; not a component or loop validation."""
import json
from itertools import product
from math import sqrt
from pathlib import Path


def frequency_hz(rt_ohm):
    # TI LM5145 equation 3: R_RT[kohm] = 10000 / F_SW[kHz].
    return 1e10 / rt_ohm


def uvlo(rhigh, rlow):
    corners = []
    for a, b, ref, ihys in product((.99, 1.01), (.99, 1.01),
                                  (1.164, 1.236), (9e-6, 11e-6)):
        on = ref * (1 + rhigh * a / (rlow * b))
        corners.append((on, on - ihys * rhigh * a))
    nominal = 1.2 * (1 + rhigh / rlow)
    return {
        "on_nominal_V": nominal, "off_nominal_V": nominal - 10e-6 * rhigh,
        "on_min_V": min(x[0] for x in corners),
        "on_max_V": max(x[0] for x in corners),
        "off_min_V": min(x[1] for x in corners),
        "off_max_V": max(x[1] for x in corners),
        "assumptions": "1% resistors; TI EN and hysteresis extremes; no leakage/TC",
    }


def feedback(rlow):
    values = [ref * (1 + 10000 * a / (rlow * b)) + ibias * 10000 * a
              for ref, a, b, ibias in product((.792, .808), (.99, 1.01),
                                            (.99, 1.01), (-1e-7, 1e-7))]
    return {"nominal_V": .8 * (1 + 10000 / rlow),
            "min_V": min(values), "max_V": max(values),
            "assumptions": "1% resistors; TI reference and FB-bias extremes; no TC"}


def buck(vin, vout, iout, inductance, fsw):
    duty = vout / vin
    ripple = vout * (1 - duty) / (inductance * fsw)
    irms = sqrt(iout ** 2 + ripple ** 2 / 12)
    return {"vin_V": vin, "vout_V": vout, "iout_A": iout,
            "L_H": inductance, "fsw_Hz": fsw, "duty": duty,
            "ripple_pp_A": ripple, "peak_A": iout + ripple / 2,
            "inductor_rms_A": irms,
            "input_cap_rms_A_ignoring_ripple": iout * sqrt(duty * (1 - duty)),
            "output_cap_rms_A": ripple / sqrt(12),
            "inductor_copper_W_25C_max_DCR": irms ** 2 * .00415,
            "inductor_copper_W_100C_estimate": irms ** 2 * .00415 * (1 + .00393 * 75),
            "mosfet_pair_conduction_W_25C_8p5mohm": irms ** 2 * .0085}


result = {
    "status": "PRELIMINARY; no EasyEDA changes; no WEBENCH/thermal/bench validation",
    "frequency": {"RT_33p2k_Hz": frequency_hz(33200),
                  "RT_133k_extrapolated_Hz_OUTSIDE_SPEC": frequency_hz(133000)},
    "uvlo_1M_34p8k": uvlo(1e6, 34800),
    "feedback_12V": feedback(715), "feedback_5V": feedback(1910),
    "buck": {},
    "precharge_ideal_R10ohm_42V": {
        str(fraction): {"bus_V": 42 * fraction,
                        "power_available_at_bus_W": 42 * fraction * (42 - 42 * fraction) / 10}
        for fraction in (.85, .95)},
    "VCC_internal_loss_example_W": (42 - 7.5) * (2 * 25e-9 * 300e3) + 42 * .0018,
}
for vout, iout in ((12, 9), (5, 5)):
    result["buck"][str(vout)] = {
        "nominal": buck(42, vout, iout, 10e-6, 300e3),
        "engineering_sweep_NOT_guaranteed_tolerance": buck(42, vout, iout, 8e-6, 270e3),
        "75V_boundary_NOT_validated_bus_envelope": buck(75, vout, iout, 8e-6, 270e3),
        "133k_extrapolation_NOT_guaranteed_operation": buck(42, vout, iout, 10e-6, frequency_hz(133000)),
    }

# Independent datasheet anchor points catch Hz/kHz and ohm/kohm mistakes.
assert frequency_hz(25000) == 400000
assert frequency_hz(100000) == 100000
assert 300000 < frequency_hz(33200) < 302000
assert 2.85 < result["buck"]["12"]["nominal"]["ripple_pp_A"] < 2.86
Path(__file__).with_name("P2B-preliminary-calculations.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False) + "\n")
print("Calculations saved; units checked against TI 100k/100kHz and 25k/400kHz.")
