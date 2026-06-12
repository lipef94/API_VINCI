# =============================================================================
# routes/qr_service.py — Génération QR Code en mémoire
# =============================================================================

import qrcode
import os
import io
from config import APP_URL, QR_BOX_SIZE, QR_BORDER, QR_ERROR_CORRECTION

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False


def _get_niveau_correction():
    return {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }.get(QR_ERROR_CORRECTION, qrcode.constants.ERROR_CORRECT_H)


def generer_qr_bytes(url=None):
    """Génère le QR code global inventaire en mémoire."""
    if url is None:
        url = f"{APP_URL}/public/inventaire"

    qr = qrcode.QRCode(
        version=None,
        error_correction=_get_niveau_correction(),
        box_size=QR_BOX_SIZE,
        border=QR_BORDER,
    )
    qr.add_data(url)
    qr.make(fit=True)

    if PIL_DISPONIBLE:
        img_qr = qr.make_image(fill_color="#1A1A1A", back_color="#FFFFFF").convert("RGB")
        img_finale = _ajouter_bandeau(img_qr, "INVENTAIRE GÉNÉRAL", "Lecture seule · temps réel")
    else:
        img_finale = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img_finale.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def generer_qr_article_bytes(article_id, article_nom, article_ref):
    """Génère un QR code pour un article spécifique (accès direct modification)."""
    url = f"{APP_URL}/scan/article/{article_id}"

    qr = qrcode.QRCode(
        version=None,
        error_correction=_get_niveau_correction(),
        box_size=QR_BOX_SIZE,
        border=QR_BORDER,
    )
    qr.add_data(url)
    qr.make(fit=True)

    if PIL_DISPONIBLE:
        img_qr = qr.make_image(fill_color="#1A1A1A", back_color="#FFFFFF").convert("RGB")
        sous_titre = f"Réf: {article_ref}"
        img_finale = _ajouter_bandeau(img_qr, article_nom[:28], sous_titre)
    else:
        img_finale = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img_finale.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def generer_qr_inventaire():
    """Compatibilité — sauvegarde aussi sur disque si possible."""
    from config import QR_DIR
    data = generer_qr_bytes()
    try:
        os.makedirs(QR_DIR, exist_ok=True)
        chemin = os.path.join(QR_DIR, "inventaire.png")
        with open(chemin, "wb") as f:
            f.write(data)
    except Exception:
        pass
    return "static/qrcodes/inventaire.png"


def _ajouter_bandeau(img_qr, titre, sous_titre=""):
    largeur_qr, hauteur_qr = img_qr.size
    bandeau_haut, bandeau_bas = 75, 50
    img_finale = Image.new("RGB", (largeur_qr, hauteur_qr + bandeau_haut + bandeau_bas), "#FFFFFF")
    img_finale.paste(img_qr, (0, bandeau_haut))
    draw = ImageDraw.Draw(img_finale)
    draw.rectangle([0, 0, largeur_qr, bandeau_haut], fill="#F5A623")
    draw.rectangle([0, hauteur_qr + bandeau_haut, largeur_qr, hauteur_qr + bandeau_haut + bandeau_bas], fill="#1A1A1A")

    font_paths_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    font_paths_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    police_titre = police_sous = police_vinci = None
    for p in font_paths_bold:
        if os.path.exists(p):
            try:
                police_titre = ImageFont.truetype(p, 18)
                police_vinci = ImageFont.truetype(p, 12)
            except Exception:
                pass
            break
    for p in font_paths_regular:
        if os.path.exists(p):
            try:
                police_sous = ImageFont.truetype(p, 11)
            except Exception:
                pass
            break
    if not police_titre: police_titre = ImageFont.load_default()
    if not police_sous:  police_sous  = ImageFont.load_default()
    if not police_vinci: police_vinci = ImageFont.load_default()

    def centrer(texte, police, y, couleur):
        bbox = draw.textbbox((0, 0), texte, font=police)
        w = bbox[2] - bbox[0]
        draw.text(((largeur_qr - w) / 2, y), texte, fill=couleur, font=police)

    centrer("SDEL Transport · Vinci Energies", police_vinci, 8, "#3A2A00")
    centrer(titre, police_titre, 26, "#1A1A1A")
    if sous_titre:
        centrer(sous_titre, police_sous, 52, "#5A3A00")
    centrer("▶  SCANNER POUR ACCÉDER", police_sous, hauteur_qr + bandeau_haut + 16, "#F5A623")
    return img_finale