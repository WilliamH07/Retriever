#!/usr/bin/env python3
"""Bloque un commit qui contient un secret. Sans dépendance (Python 3 seul).

Usage : secret_scan.py            -> analyse les changements indexés (git add)
        secret_scan.py --all      -> analyse aussi tout l'historique git
Les valeurs trouvées ne sont jamais affichées en entier.
"""
import os, re, subprocess, sys

PATTERNS = {
    "clé OpenAI/Anthropic": r"sk-(?:proj-|ant-)?[A-Za-z0-9_\-]{32,}",
    "clé AWS": r"AKIA[0-9A-Z]{16}",
    "jeton GitHub": r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}",
    "jeton Slack": r"xox[baprs]-[A-Za-z0-9\-]{10,}",
    "clé Google": r"AIza[0-9A-Za-z_\-]{35}",
    "clé Stripe live": r"[sr]k_live_[A-Za-z0-9]{20,}",
    "clé privée": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----\s*[\r\n\\]*[A-Za-z0-9+/]{20,}",
    "JWT": r"eyJ[A-Za-z0-9_\-]{15,}\.eyJ[A-Za-z0-9_\-]{15,}\.[A-Za-z0-9_\-]{10,}",
    "jeton fournisseur": r"(?:gsk_|hf_|r8_|pplx-|xai-)[A-Za-z0-9]{20,}",
    "clé Mapbox": r"pk\.eyJ[A-Za-z0-9_\-]{20,}",
    "affectation suspecte": r"""(?i)(?:api[_-]?key|secret|token|passw(?:or)?d|service_role)["']?\s*[:=]\s*["']([A-Za-z0-9_\-/+=.]{16,})["']""",
}
RX = {k: re.compile(v) for k, v in PATTERNS.items()}
PLACEHOLDER = re.compile(r"(?i)(your|example|placeholder|changeme|xxx|<|\$\{|process\.env|os\.environ|getenv|dummy|fake|\*\*\*|\.\.\.|\bnull\b|\bnone\b)")
FORBIDDEN_FILES = re.compile(r"(^|/)\.env($|\.(?!example|sample|template))|\.(pem|p12|pfx|key|jks|keystore|mobileprovision)$|(^|/)id_(rsa|ed25519)|service-account.*\.json$|GoogleService-Info\.plist$")
SKIP = re.compile(r"(node_modules/|package-lock\.json|\.lock$|\.min\.js$|\.(png|jpe?g|gif|pdf|zip|gz|ico|woff2?|mp4|bin|a|o|dylib|xcresult)$)")
ALLOW_MARK = "secret-scan:allow"  # à mettre en commentaire sur une ligne volontairement factice

def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, errors="ignore").stdout

def mask(v): return v[:4] + "…(" + str(len(v)) + " car.)"

def findings(line):
    if ALLOW_MARK in line or len(line) > 3000: return
    for name, rx in RX.items():
        m = rx.search(line)
        if m:
            v = m.group(1) if m.groups() else m.group(0)
            if not PLACEHOLDER.search(v): yield name, mask(v)

def scan_diff(cmd):
    bad, fn = [], ""
    for l in git(*cmd).split("\n"):
        if l.startswith("+++ "): fn = l[6:]
        elif l.startswith("+") and not l.startswith("+++") and not SKIP.search(fn):
            for name, v in findings(l[1:]): bad.append((fn, name, v))
    return bad

def main():
    root = git("rev-parse", "--show-toplevel").strip()
    if root: os.chdir(root)
    names = [f for f in git("diff", "--cached", "--name-only", "--diff-filter=ACM").split("\n") if f]
    bad = [(f, "fichier sensible", f) for f in names if FORBIDDEN_FILES.search(f)]
    bad += scan_diff(["diff", "--cached", "-U0", "--no-color"])
    if "--all" in sys.argv:
        bad += scan_diff(["log", "--all", "-p", "-U0", "--no-color", "--format="])
    if bad:
        print("\n❌ Commit bloqué : secret potentiel détecté\n", file=sys.stderr)
        for f, name, v in sorted(set(bad)): print(f"  - {name} dans {f} ({v})", file=sys.stderr)
        print("\nRetire la valeur (variable d'environnement + .env.example), puis recommence.\n"
              "Si c'est un faux positif voulu : ajoute `secret-scan:allow` en commentaire sur la ligne.\n"
              "Si la clé a déjà été exposée : révoque-la chez le fournisseur AVANT tout.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__": main()
