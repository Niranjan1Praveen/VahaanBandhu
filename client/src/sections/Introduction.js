"use client";
import Tags from "@/components/ui/tags";
import { useMotionValueEvent, useScroll, useTransform } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { twMerge } from "tailwind-merge";

const text = `असंगठित लॉजिस्टिक्स, ऊँची परिवहन लागत और समय पर ट्रक की अनुपलब्धता के कारण, किसानों को देरी, फसल खराब होने और तकनीकी पहुँच की कमी जैसी गंभीर समस्याओं का सामना करना पड़ता है।`;

const words = text.split(" ");
export default function Introduction() {
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
            <Tags title={"परिचय"} />
          </div>
          <div className="text-4xl md:text-5xl text-center font-medium mt-10">
            <span>
              सामाजिक प्रभाव को मापने योग्य और सार्थक होना चाहिए। CSR फंडिंग के
              बढ़ने के बावजूद...
            </span>{" "}
            <span className="text-white/15 leading-relaxed tracking-wider">
              {words.map((word, index) => {
                const isVisible = index < currentWord;
                
                const shouldHighlight =
                  isVisible &&
                  ["असंगठित", "देरी", "खराब"].some((w) =>
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
              इसीलिए हमने वाहनबन्धु बनाया है।
            </span>
          </div>
        </div>
        <div className="h-[150vh]" ref={scrollTarget}></div>
      </div>
    </section>
  );
}
