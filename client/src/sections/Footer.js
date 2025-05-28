import Image from "next/image";
import Link from "next/link";
import logo from "@/assets/images/logo.png";

const footerLinks = [
  { href: "#", label: "संपर्क करें" },
  { href: "#", label: "गोपनीयता नीति" },
  { href: "#", label: "नियम और शर्तें" },
];


export default function Footer() {
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
            द्वारा निर्मित{" "}
            <Link href={"/"} className="uppercase">
              code4change
            </Link>
            । स्रोत कोड{" "}
            <Link
              href={
                "https://github.com/Niranjan1Praveen/DropConnect-Development"
              }
              className="underline italic"
            >
              GitHub
            </Link>{" "}
            पर उपलब्ध है।
          </small>
        </div>
        <nav className="flex gap-6">
          {footerLinks.map((link) => (
            <a
              href={link.href}
              key={link.label}
              className="text-white/50 text-sm"
            >
              {link.label}
            </a>
          ))}
        </nav>
      </footer>
    </section>
  );
}
