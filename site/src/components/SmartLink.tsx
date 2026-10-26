import Link from "next/link";
import type { ComponentProps } from "react";

import { isExterno } from "@/lib/format";

/** Link do CMS: interno (navegação do Next.js) ou externo (novo separador). */
export function SmartLink({ href, ...props }: Omit<ComponentProps<"a">, "href"> & { href: string }) {
  if (isExterno(href)) {
    const novaJanela = href.startsWith("http");
    return <a href={href} {...(novaJanela ? { target: "_blank", rel: "noopener noreferrer" } : {})} {...props} />;
  }
  return <Link href={href || "/"} {...props} />;
}
