"use client";
import { t } from "@/lib/i18n";
import { useSession } from "@/components/providers/SessionProvider";
import Image from "next/image";
import Link from "next/link";
import logo from "@/assets/images/logo.png";

const footerLinks = [
  { href: "#", key: "footer.contact" },
  { href: "#", key: "footer.privacy" },
  { href: "#", key: "footer.terms" },
];


export default function Footer() {
  const { lang } = useSession();
  const tr = (k) => t(k, lang);
  return (
    <section className="py-10 px-4 flex items-center justify-center">
      <footer className="container flex flex-col md:flex-row md:justify-between items-center gap-6">
        <div className="flex flex-col gap-2 items-center text-center md:items-start">
          <div className="flex items-center">
            <Image src={logo} alt="Logo Icon" className="h-auto w-20" />
            <h2 className="font-bold text-2xl md:inline-flex hidden text-lime-400">
              वाहनबन्धु
            </h2>
          </div>
          <small className="text-white/50">
            {tr("footer.builtBy")}{" "}
            <Link href={"/"} className="uppercase">
              code4change
            </Link>
            {tr("footer.sourceCode")}{" "}
            <Link
              href={
                "https://github.com/Niranjan1Praveen/DropConnect-Development"
              }
              className="underline italic"
            >
              GitHub
            </Link>{" "}
            {tr("footer.availableOn")}
          </small>
        </div>
        <nav className="flex gap-6">
          {footerLinks.map((link) => (
            <a
              href={link.href}
              key={link.key}
              className="text-white/50 text-sm"
            >
              {tr(link.key)}
            </a>
          ))}
        </nav>
      </footer>
    </section>
  );
}
