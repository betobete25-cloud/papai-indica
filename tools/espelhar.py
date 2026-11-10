"""Espelha a lojinha do Claude (artifact) no site opapaiindica.com.br.

Uso: python3 -I tools/espelhar.py <index.html do artifact> <pasta com as fotos <hash>.webp>
Roda na raiz do repositório. Mantém o <head> do site, troca /_blob/<hash> por
img/<id do item>.webp (a foto do topo vira img/roberto.webp) e apaga de img/ o que
nenhum item usa mais.
"""
import json, os, re, shutil, sys

AVATAR = "img/roberto.webp"

def main(src, blobs):
    s = open(src, encoding="utf8").read()
    if "</style></head><body>" in s:  # tira o esqueleto que o Artifact devolve
        s = s.split("</style></head><body>", 1)[1]
    s = s.rsplit("</body></html>", 1)[0].strip("\n")
    m = re.search(r'id="ofertas">(.*?)</script>', s, re.S)
    dados = json.loads(m.group(1))
    mapa = {}
    for it in dados["itens"]:
        f = it.get("foto") or ""
        if f.startswith("/_blob/"):
            mapa[f[7:]] = "img/" + re.sub(r"[^\w-]", "-", it["id"]) + ".webp"
    av = re.search(r'class="avatar"><img src="/_blob/([0-9a-f]{32})"', s)
    if av:
        mapa[av.group(1)] = AVATAR
    os.makedirs("img", exist_ok=True)
    for h, dest in mapa.items():
        orig = os.path.join(blobs, h + ".webp")
        if dest == AVATAR and os.path.exists(AVATAR):
            pass
        elif os.path.exists(orig):
            shutil.copyfile(orig, dest)
        elif not os.path.exists(dest):
            print("FALTA FOTO", h, dest)
        s = s.replace("/_blob/" + h, dest)
    resto = re.findall(r"/_blob/[0-9a-f]{32}", s)
    if resto:
        sys.exit("fotos sem destino: %s" % resto[:5])
    s = s.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    atual = open("index.html", encoding="utf8").read()
    head = atual.split("<title>", 1)[0]
    i = s.index('<header class="board">')
    novo = head + s[:i] + "</head>\n<body>\n" + s[i:] + "\n</body>\n</html>\n"
    open("index.html", "w", encoding="utf8").write(novo)
    usados = set(re.findall(r"img/([\w-]+\.webp)", novo))
    for f in os.listdir("img"):
        if f not in usados:
            os.remove(os.path.join("img", f))
    print("ok:", len(dados["itens"]), "itens,", len(usados), "fotos, atualizado", dados["atualizado"])

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
