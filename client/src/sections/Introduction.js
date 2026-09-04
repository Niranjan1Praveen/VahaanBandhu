"use client";
import { t } from "@/lib/i18n";
import { useSession } from "@/components/providers/SessionProvider";
import Tags from "@/components/ui/tags";
import { useMotionValueEvent, useScroll, useTransform } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { twMerge } from "tailwind-merge";

// Word-by-word animation source. Read from the dictionary so it
// switches with the language like every other string.
const TEXT_KEY = "intro.problem";

export default function Introduction() {
  const { lang } = useSession();
  const tr = (k) => t(k, lang);
  // Recomputed per render so the animated text follows the language.
  const words = tr(TEXT_KEY).split(" ");
  const scrollTarget = useRef();
  const { scrollYProgress } = useScroll({
    target: scrollTarget,
    offset: ["start end", "end end"],
  });
  const [currentWord, setCurrentWord] = useState(0);
  const wordIndex = useTransform(scrollYProgress, [0, 1], [0, words.length]);
  useEffect(() => {
    wordIndex.on("change", (latest) => {
      setCurrentWord(latest);
    });
  }, [wordIndex]);
  return (
    <section className="py-28 px-4 lg:py-40 flex items-center justify-center" id="introductions">
      <div className="container">
        <div className="sticky top-20 md:top-28 lg:top-40">
          <div className="flex justify-center">
            <Tags title={tr("intro.tag")} />
          </div>
          <div className="text-4xl md:text-5xl text-center font-medium mt-10">
            <span>
              {tr("intro.csr")}
            </span>{" "}
            <span className="text-white/15 leading-relaxed tracking-wider">
              {words.map((word, index) => {
                const isVisible = index < currentWord;
                
                const shouldHighlight =
                  isVisible &&
                  (lang === "hi" ? ["असंगठित", "देरी", "खराब"] : ["Disorganised", "delays", "spoiled"]).some((w) =>
                    word.toLowerCase().includes(w)
                  );

                return (
                  <span
                    key={index}
                    className={twMerge(
                      "transition duration-500",
                      isVisible ? "text-white" : "text-white/15",
                      isVisible && shouldHighlight && "text-red-500 italic",
                    )}
                  >
                    {word + " "}
                  </span>
                );
              })}
            </span>
            <span className="text-lime-400 block mt-3">
              {tr("intro.closing")}
            </span>
          </div>
        </div>
        <div className="h-[150vh]" ref={scrollTarget}></div>
      </div>
    </section>
  );
}
