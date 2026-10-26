"""Representação das imagens na API: renditions WebP em vários tamanhos para `srcset`."""

from django.conf import settings

LARGURAS = (480, 960, 1600)


def _absoluto(url: str) -> str:
    if url.startswith("/"):
        return settings.API_PUBLIC_URL.rstrip("/") + url
    return url


def imagem_api(image, quadrado: bool = False):
    if image is None:
        return None
    if quadrado:
        specs = [f"fill-{w}x{w}-c80|format-webp" for w in (320, 640)]
    else:
        specs = [f"width-{w}|format-webp" for w in LARGURAS]
    renditions = image.get_renditions(*specs)
    srcset = [(_absoluto(r.url), r.width) for r in renditions.values()]
    maior = max(srcset, key=lambda item: item[1])
    return {
        "id": image.pk,
        "alt": image.default_alt_text or image.title,
        "url": maior[0],
        "largura": image.width,
        "altura": image.height,
        "srcset": ", ".join(f"{url} {w}w" for url, w in srcset),
        "foco": {"x": image.focal_point_x, "y": image.focal_point_y} if image.has_focal_point() else None,
    }
