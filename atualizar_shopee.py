import os
import time
import json
import hashlib
import urllib.request
import html
import re

APP_ID = os.environ["SHOPEE_APP_ID"]
SECRET = os.environ["SHOPEE_SECRET"]

URL = "https://open-api.affiliate.shopee.com.br/graphql"

query = """
query {
  productOfferV2(
    listType: 0
    sortType: 2
    page: 1
    limit: 5
  ) {
    nodes {
      productName
      price
      imageUrl
      productLink
      offerLink
      priceMin
      priceMax
      priceDiscountRate
      commissionRate
      commission
    }
  }
}
"""

payload = json.dumps(
    {"query": query, "variables": {}},
    separators=(",", ":")
)

timestamp = int(time.time())

signature_string = f"{APP_ID}{timestamp}{payload}{SECRET}"

signature = hashlib.sha256(
    signature_string.encode("utf-8")
).hexdigest()

authorization = (
    f"SHA256 Credential={APP_ID}, "
    f"Timestamp={timestamp}, "
    f"Signature={signature}"
)

request = urllib.request.Request(
    URL,
    data=payload.encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": authorization
    },
    method="POST"
)

with urllib.request.urlopen(request) as response:
    resultado = json.loads(response.read().decode("utf-8"))

if "errors" in resultado:
    print("ERRO DA SHOPEE:")
    print(json.dumps(resultado["errors"], indent=2, ensure_ascii=False))
    raise SystemExit(1)

produtos = resultado["data"]["productOfferV2"]["nodes"][:5]

if len(produtos) < 5:
    raise SystemExit(
        f"A Shopee retornou apenas {len(produtos)} produtos. "
        "O index.html não será alterado."
    )

# Salva uma cópia dos dados recebidos
with open("produtos_shopee.json", "w", encoding="utf-8") as arquivo:
    json.dump(produtos, arquivo, ensure_ascii=False, indent=2)


def formatar_preco(valor):
    try:
        numero = float(valor)
        return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return f"R$ {valor}"


def criar_card(produto, numero):
    nome = html.escape(str(produto.get("productName") or "Oferta Shopee"))
    imagem = html.escape(str(produto.get("imageUrl") or ""), quote=True)

    # offerLink é preferido por ser o link de oferta retornado pela API de afiliados.
    link = produto.get("offerLink") or produto.get("productLink") or ""
    link = html.escape(str(link), quote=True)

    preco = formatar_preco(produto.get("price") or produto.get("priceMin") or "0")

    nome_busca = html.escape(
        re.sub(r"\s+", " ", str(produto.get("productName") or "oferta shopee")).lower(),
        quote=True
    )

    desconto = produto.get("priceDiscountRate")
    categoria = "Oferta • Shopee"

    if desconto not in (None, "", 0, "0"):
        categoria = f"Oferta Shopee • {html.escape(str(desconto))}% OFF"

    return f"""<!-- SHOPEE {numero} -->

<article class="card"
data-store="shopee"
data-category="ofertas"
data-name="{nome_busca}">

<div class="image-box">
<span class="store shopee">SHOPEE</span>
<img src="{imagem}" alt="{nome}" loading="lazy">
</div>

<div class="card-content">

<div class="category">{categoria}</div>

<h3>{nome}</h3>

<p class="description">
Oferta encontrada automaticamente pela Clout Promoções. Confira preço, frete, estoque e condições diretamente na Shopee.
</p>

<span class="price-label">Preço informado</span>
<div class="price">{preco}</div>

<a
href="{link}"
target="_blank"
rel="noopener sponsored"
class="offer-btn">
VER NA SHOPEE
</a>

</div>
</article>"""


novos_cards = "\n\n".join(
    criar_card(produto, numero)
    for numero, produto in enumerate(produtos, 1)
)

with open("index.html", "r", encoding="utf-8") as arquivo:
    site = arquivo.read()

inicio = site.find("<!-- SHOPEE 1 -->")
fim = site.find("<!-- MERCADO LIVRE 1 -->")

if inicio == -1 or fim == -1 or fim <= inicio:
    raise SystemExit(
        "Marcadores dos produtos não encontrados. "
        "O index.html não foi alterado."
    )

novo_site = (
    site[:inicio]
    + novos_cards
    + "\n\n\n"
    + site[fim:]
)

with open("index.html", "w", encoding="utf-8") as arquivo:
    arquivo.write(novo_site)

print("SUCESSO!")
print("5 produtos da Shopee foram inseridos no index.html.")

for numero, produto in enumerate(produtos, 1):
    print(
        f"{numero}. {produto.get('productName')} | "
        f"{formatar_preco(produto.get('price') or produto.get('priceMin'))}"
    )
