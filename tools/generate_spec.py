"""
Genere les fichiers de specification partages par toutes les librairies :

    spec/cipher_tables.json   tables de substitution (password, decode) + table sin
    spec/test_vectors.json    univers DMX -> trame chiffree attendue (octet pour octet)

La SEULE source utilisee est tools/reference/cipher_reference.py : le portage Python
de Code.java (appli Android RY-AI) dont les trames ont ete validees sur le vrai
boitier (test de clignotement). Toutes les librairies (Python, C, C#, Java) sont
testees contre ces vecteurs : si elles produisent les memes octets, elles parlent
au boitier exactement comme l'appli d'origine.

Usage :  python tools/generate_spec.py
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent / "reference"))

import cipher_reference as ref  # noqa: E402

FRAME_LEN = 521
UNIVERSE_SIZE = 512
PAYLOAD_START = 5
MARKER_OFFSET = 517


def build_reference_frame(universe, code_num, scene=0, speed=0):
    """Construit une trame avec l'implementation de reference (universe = 512 octets, index 0 = canal 1)."""
    buf = bytearray(FRAME_LEN)
    buf[0] = 0x00
    buf[1], buf[2] = ord("K"), ord("T")
    buf[3], buf[4] = scene, speed
    buf[PAYLOAD_START:PAYLOAD_START + UNIVERSE_SIZE] = bytes(universe)
    buf[519], buf[520] = ord("T"), ord("K")
    return ref.encryption1(buf, PAYLOAD_START, UNIVERSE_SIZE, code_num, MARKER_OFFSET)


def universe_from(channels):
    """channels : dict {numero_de_canal (1..512): valeur}."""
    universe = [0] * UNIVERSE_SIZE
    for ch, value in channels.items():
        universe[ch - 1] = value
    return universe


def vectors():
    rng = random.Random(2026)
    cases = [
        ("tout_a_zero", "Univers vide.", [0] * UNIVERSE_SIZE, 0),
        ("reference_code1",
         "Canal 1=255, 2=128, 3=1, 14=42, 512=7 (meme trame que les tests de DmxController).",
         universe_from({1: 255, 2: 128, 3: 1, 14: 42, 512: 7}), 1),
        ("rampe_code42", "Canal n = (n * 7) mod 256.", [(n * 7) % 256 for n in range(1, UNIVERSE_SIZE + 1)], 42),
        ("plein_code128", "Tous les canaux a 255.", [255] * UNIVERSE_SIZE, 128),
        ("aleatoire_code255", "Valeurs pseudo-aleatoires (graine 2026).",
         [rng.randrange(256) for _ in range(UNIVERSE_SIZE)], 255),
        ("mindi_spider_adresse1_code7",
         "Mini Spider regle sur l'adresse 1 (il ecoute a partir du canal 2) : ailes en miroir, "
         "dimmer 100 %, LED 1 et 5 (rouges supposees) a fond.",
         universe_from({2: 200, 3: 55, 4: 255, 6: 255, 10: 255}), 7),
    ]
    out = []
    for name, description, universe, code_num in cases:
        frame = build_reference_frame(universe, code_num)
        out.append({
            "name": name,
            "description": description,
            "code_num": code_num,
            "scene": 0,
            "speed": 0,
            "universe_hex": bytes(universe).hex(),
            "frame_hex": bytes(frame).hex(),
        })
    return out


def main():
    spec = ROOT / "spec"
    spec.mkdir(exist_ok=True)

    tables = {
        "_comment": "Tables du brouillage JL_SPP DMX (Code.java de l'appli RY-AI). "
                    "password[k][v] = octet brouille ; decode[k] = permutation inverse de password[k] ; "
                    "sin = table de 256 valeurs (choix de la table : sin[codeNum] % 5).",
        "password": ref.password,
        "decode": ref.decode,
        "sin": ref.sin,
    }
    (spec / "cipher_tables.json").write_text(json.dumps(tables, indent=1), encoding="utf-8")

    data = {
        "_comment": "Vecteurs de test : univers (512 octets, index 0 = canal DMX 1) -> trame de 521 octets "
                    "attendue. Generes par tools/generate_spec.py depuis l'implementation validee sur le materiel.",
        "frame_length": FRAME_LEN,
        "universe_size": UNIVERSE_SIZE,
        "handshake_connect_hex": "bb9977017799",
        "handshake_disconnect_hex": "bb7799109977" + "0055",
        "vectors": vectors(),
    }
    (spec / "test_vectors.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"spec/cipher_tables.json et spec/test_vectors.json ({len(data['vectors'])} vecteurs) generes.")


if __name__ == "__main__":
    main()
