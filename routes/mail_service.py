# =============================================================================
# routes/mail_service.py — Notifications email via Brevo API
# =============================================================================

import os
import json
import urllib.request
import urllib.error
from config import MAIL_FROM, MAIL_ALERT_TO, APP_URL

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")


def envoyer_alerte_stock(article_nom, article_ref, quantite, quantite_min,
                          emplacement="", magasin="", operateur="Système",
                          destinataires=None):
    """
    Envoie un email d'alerte via l'API Brevo (HTTP — fonctionne sur Render gratuit).
    """
    if not destinataires:
        if MAIL_ALERT_TO:
            destinataires = [e.strip() for e in MAIL_ALERT_TO.split(",") if e.strip()]
        else:
            print(f"[MAIL] Aucun destinataire — {article_nom}")
            return False

    if not BREVO_API_KEY:
        print("[MAIL] BREVO_API_KEY manquante")
        return False

    statut = "RUPTURE" if quantite == 0 else "STOCK BAS"
    couleur_badge = "#D32F2F" if quantite == 0 else "#E65100"

    corps_html = f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F0F0F0;font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:560px;margin:32px auto;background:#FAFAFA;border-top:4px solid #F5A623;">
    <div style="background:#1A1A1A;padding:18px 24px;">
      <div style="background:#F5A623;color:#1A1A1A;font-weight:700;font-size:13px;padding:4px 10px;letter-spacing:1px;display:inline-block;">SDEL</div>
      <div style="color:#FAFAFA;font-weight:700;font-size:15px;margin-top:6px;">Alerte Inventaire</div>
      <div style="color:#888;font-size:11px;font-family:monospace;">Vinci Energies · Gestion des Stocks</div>
    </div>
    <div style="background:{couleur_badge};color:white;text-align:center;padding:10px;font-weight:700;font-size:13px;letter-spacing:1px;">
      ⚠ {statut}
    </div>
    <div style="padding:24px;">
      <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:20px;">
        <tr style="background:#F5F5F5;">
          <td style="padding:10px 14px;font-weight:600;color:#555;border-bottom:1px solid #E0E0E0;width:40%;">Article</td>
          <td style="padding:10px 14px;color:#1A1A1A;border-bottom:1px solid #E0E0E0;font-weight:700;">{article_nom}</td>
        </tr>
        <tr>
          <td style="padding:10px 14px;font-weight:600;color:#555;border-bottom:1px solid #E0E0E0;">Référence</td>
          <td style="padding:10px 14px;color:#1A1A1A;border-bottom:1px solid #E0E0E0;font-family:monospace;">{article_ref}</td>
        </tr>
        <tr style="background:#F5F5F5;">
          <td style="padding:10px 14px;font-weight:600;color:#555;border-bottom:1px solid #E0E0E0;">Stock actuel</td>
          <td style="padding:10px 14px;color:{couleur_badge};border-bottom:1px solid #E0E0E0;font-weight:700;font-size:18px;">{quantite}</td>
        </tr>
        <tr>
          <td style="padding:10px 14px;font-weight:600;color:#555;border-bottom:1px solid #E0E0E0;">Seuil minimum</td>
          <td style="padding:10px 14px;color:#1A1A1A;border-bottom:1px solid #E0E0E0;">{quantite_min}</td>
        </tr>
        <tr style="background:#F5F5F5;">
          <td style="padding:10px 14px;font-weight:600;color:#555;border-bottom:1px solid #E0E0E0;">Opérateur</td>
          <td style="padding:10px 14px;color:#1A1A1A;border-bottom:1px solid #E0E0E0;">{operateur}</td>
        </tr>
        {"<tr><td style='padding:10px 14px;font-weight:600;color:#555;border-bottom:1px solid #E0E0E0;'>Emplacement</td><td style='padding:10px 14px;color:#1A1A1A;border-bottom:1px solid #E0E0E0;'>" + emplacement + "</td></tr>" if emplacement else ""}
        {"<tr style='background:#F5F5F5;'><td style='padding:10px 14px;font-weight:600;color:#555;border-bottom:1px solid #E0E0E0;'>Magasin</td><td style='padding:10px 14px;color:#1A1A1A;border-bottom:1px solid #E0E0E0;'>" + magasin + "</td></tr>" if magasin else ""}
      </table>
      <div style="text-align:center;margin-top:16px;">
        <a href="{APP_URL}/inventaire" style="background:#F5A623;color:#1A1A1A;padding:10px 24px;font-weight:700;text-decoration:none;border-radius:3px;display:inline-block;">
          Accéder à l'inventaire →
        </a>
      </div>
    </div>
    <div style="background:#1A1A1A;padding:12px 24px;text-align:center;">
      <p style="color:#555;font-size:11px;margin:0;font-family:monospace;">
        SDEL Transport Services · VINCI Energies<br>
        Message automatique — ne pas répondre
      </p>
    </div>
  </div>
</body>
</html>
"""

    expediteur_email = MAIL_FROM or "noreply@sdel.fr"
    expediteur_nom   = "SDEL Inventory"

    payload = {
        "sender": {"name": expediteur_nom, "email": expediteur_email},
        "to": [{"email": d} for d in destinataires],
        "subject": f"⚠ Stock bas — {article_nom} ({article_ref})",
        "htmlContent": corps_html
    }

    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=data,
        headers={
            "accept":       "application/json",
            "content-type": "application/json",
            "api-key":      BREVO_API_KEY,
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"[MAIL] Alerte Brevo envoyée à {destinataires} — {article_nom} : {quantite} restants")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[MAIL] Erreur Brevo {e.code} : {body}")
        return False
    except Exception as e:
        print(f"[MAIL] Erreur : {e}")
        return False
