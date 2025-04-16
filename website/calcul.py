from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from numpy import log as Ln, exp as e

calcul = Blueprint("calcul", __name__)

CONSTANTS = {
    'V_exp': 1.33e-05,
    'aBA': 194.5302,
    'aAB': -10.7575,
    'lambda_A': 1.127,
    'lambda_B': 0.973,
    'qA': 1.432,
    'qB': 1.4,
    'D_AB': 2.1e-5,
    'D_BA': 2.67e-5
}

def calcul_diffusion(Xa, T):
    if not (0 <= Xa <= 1):
        raise ValueError("La fraction Xa doit être entre 0 et 1")
    if T <= 0:
        raise ValueError("La température doit être positive")
    Xb = 1 - Xa
    phiA = (Xa * CONSTANTS['lambda_A']) / (Xa * CONSTANTS['lambda_A'] + Xb * CONSTANTS['lambda_B'])
    phiB = 1 - phiA
    tauxAB = e(-CONSTANTS['aAB'] / T)
    tauxBA = e(-CONSTANTS['aBA'] / T)
    tetaA = (Xa * CONSTANTS['qA']) / (Xa * CONSTANTS['qA'] + Xb * CONSTANTS['qB'])
    tetaB = 1 - tetaA
    tetaAA = tetaA / (tetaA + tetaB * tauxBA)
    tetaBB = tetaB / (tetaB + tetaA * tauxAB)
    tetaAB = (tetaA * tauxAB) / (tetaA * tauxAB + tetaB)
    tetaBA = (tetaB * tauxBA) / (tetaB * tauxBA + tetaA)
    termes = (
        Xb * Ln(CONSTANTS['D_AB']) +
        Xa * Ln(CONSTANTS['D_BA']) +
        2 * (Xa * Ln(Xa / phiA) + Xb * Ln(Xb / phiB)) +
        2 * Xb * Xa * (
            (phiA / Xa) * (1 - CONSTANTS['lambda_A'] / CONSTANTS['lambda_B']) +
            (phiB / Xb) * (1 - CONSTANTS['lambda_B'] / CONSTANTS['lambda_A'])
        ) +
        Xb * CONSTANTS['qA'] * (
            (1 - tetaBA ** 2) * Ln(tauxBA) +
            (1 - tetaBB ** 2) * tauxAB * Ln(tauxAB)
        ) +
        Xa * CONSTANTS['qB'] * (
            (1 - tetaAB ** 2) * Ln(tauxAB) +
            (1 - tetaAA ** 2) * tauxBA * Ln(tauxBA)
        )
    )
    solution = e(termes)
    erreur = (abs(solution - CONSTANTS['V_exp']) / CONSTANTS['V_exp']) * 100
    return {
        'lnDab': termes,
        'Dab': solution,
        'erreur': erreur,
        'Xa': Xa,
        'T': T
    }

@calcul.route("/calcul", methods=["GET", "POST"])
@login_required
def calcul_route():
    if request.method == "POST":
        try:
            Xa = float(request.form.get("Xa"))
            T = float(request.form.get("T"))

            return redirect(url_for("calcul.result_route", Xa=Xa, T=T))
        except (TypeError, ValueError) as e:
            flash(str(e), "error")
            return render_template("calcul.html")
    return render_template("calcul.html", user=current_user)

@calcul.route("/result")
@login_required
def result_route():
    try:
        Xa = float(request.args.get("Xa", ""))
        T = float(request.args.get("T", ""))
        data = calcul_diffusion(Xa, T)
        error = None
        # Format numerical outputs in scientific notation
        formatted_data = {
            'lnDab': f"{data['lnDab']:.2e}",
            'Dab': f"{data['Dab']:.2e}",
            'erreur': f"{data['erreur']:.2e}",
            'Xa': data['Xa'],  # You can also format these if needed
            'T': data['T']
        }
    except Exception as e:
        error = str(e)
        formatted_data = None
    return render_template("result.html", result=formatted_data, error=error, user=current_user)
