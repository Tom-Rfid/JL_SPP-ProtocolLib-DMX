"""
Genere, a partir de spec/cipher_tables.json et spec/test_vectors.json, les fichiers
de tables propres a chaque langage (ne pas les modifier a la main) :

    python/src/jlspp_dmx/_tables.py
    c/src/jlspp_tables.c
    c/tests/test_vectors.h
    csharp/src/JlSpp.Dmx/CipherTables.g.cs
    android/jlspp-dmx/src/main/java/io/github/tomrfid/jlsppdmx/CipherTables.java

Usage :  python tools/generate_spec.py && python tools/generate_tables.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = "Fichier GENERE par tools/generate_tables.py depuis spec/cipher_tables.json - ne pas modifier."


def rows(values, per_line=16, indent="    "):
    lines = []
    for i in range(0, len(values), per_line):
        lines.append(indent + ", ".join(str(v) for v in values[i:i + per_line]) + ",")
    return "\n".join(lines)


def write(path, text):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print("ecrit :", path.relative_to(ROOT))


def python_tables(t):
    def table(name, data):
        inner = "\n".join(f"    bytes([\n{rows(row, indent='        ')}\n    ])," for row in data)
        return f"{name} = (\n{inner}\n)\n"
    return (f'"""{HEADER}"""\n\n'
            + table("PASSWORD", t["password"]) + "\n"
            + table("DECODE", t["decode"]) + "\n"
            + f"SIN = bytes([\n{rows(t['sin'])}\n])\n")


def c_tables(t):
    def table(name, data):
        inner = "\n".join("    {\n" + rows(row, indent="        ") + "\n    }," for row in data)
        return f"const uint8_t {name}[5][256] = {{\n{inner}\n}};\n"
    return (f"/* {HEADER} */\n\n#include <stdint.h>\n\n"
            + table("jlspp_password", t["password"]) + "\n"
            + table("jlspp_decode", t["decode"]) + "\n"
            + f"const uint8_t jlspp_sin[256] = {{\n{rows(t['sin'])}\n}};\n")


def c_test_vectors(v):
    items = []
    for vec in v["vectors"]:
        universe = list(bytes.fromhex(vec["universe_hex"]))
        frame = list(bytes.fromhex(vec["frame_hex"]))
        items.append(
            "    {\n"
            f"        \"{vec['name']}\", {vec['code_num']},\n"
            f"        {{\n{rows(universe, indent='            ')}\n        }},\n"
            f"        {{\n{rows(frame, indent='            ')}\n        }},\n"
            "    },")
    return (f"/* Fichier GENERE par tools/generate_tables.py depuis spec/test_vectors.json - ne pas modifier. */\n"
            "#ifndef JLSPP_TEST_VECTORS_H\n#define JLSPP_TEST_VECTORS_H\n\n#include <stdint.h>\n\n"
            "typedef struct {\n    const char *name;\n    uint8_t code_num;\n"
            "    uint8_t universe[512];\n    uint8_t frame[521];\n} jlspp_test_vector;\n\n"
            "static const jlspp_test_vector JLSPP_TEST_VECTORS[] = {\n" + "\n".join(items) + "\n};\n\n"
            f"#define JLSPP_TEST_VECTOR_COUNT {len(v['vectors'])}\n\n#endif\n")


def csharp_tables(t):
    def table(name, data):
        inner = "\n".join("            new byte[]\n            {\n" + rows(row, indent="                ") + "\n            },"
                          for row in data)
        return f"        internal static readonly byte[][] {name} =\n        {{\n{inner}\n        }};\n"
    return (f"// {HEADER}\n\nnamespace JlSpp.Dmx\n{{\n    internal static class CipherTables\n    {{\n"
            + table("Password", t["password"]) + "\n"
            + table("Decode", t["decode"]) + "\n"
            + f"        internal static readonly byte[] Sin =\n        {{\n{rows(t['sin'], indent='            ')}\n        }};\n"
            + "    }\n}\n")


def java_tables(t):
    def table(name, data):
        inner = "\n".join("        {\n" + rows(row, indent="            ") + "\n        }," for row in data)
        return f"    static final int[][] {name} = {{\n{inner}\n    }};\n"
    return (f"// {HEADER}\npackage io.github.tomrfid.jlsppdmx;\n\n"
            "/** Tables du brouillage (valeurs 0..255 stockees en int : les byte Java sont signes). */\n"
            "final class CipherTables {\n    private CipherTables() {}\n\n"
            + table("PASSWORD", t["password"]) + "\n"
            + table("DECODE", t["decode"]) + "\n"
            + f"    static final int[] SIN = {{\n{rows(t['sin'], indent='        ')}\n    }};\n}}\n")


def main():
    tables = json.loads((ROOT / "spec" / "cipher_tables.json").read_text(encoding="utf-8"))
    vectors = json.loads((ROOT / "spec" / "test_vectors.json").read_text(encoding="utf-8"))

    write("python/src/jlspp_dmx/_tables.py", python_tables(tables))
    write("c/src/jlspp_tables.c", c_tables(tables))
    write("c/tests/test_vectors.h", c_test_vectors(vectors))
    write("csharp/src/JlSpp.Dmx/CipherTables.g.cs", csharp_tables(tables))
    write("android/jlspp-dmx/src/main/java/io/github/tomrfid/jlsppdmx/CipherTables.java", java_tables(tables))


if __name__ == "__main__":
    main()
